import json
import os
from pathlib import Path
from statistics import mean
import tomllib

from openai import OpenAI


ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evaluation"
PROMPTS_FILE = EVAL_DIR / "benchmark_prompts.json"
RESULT_FILE = EVAL_DIR / "report.json"
MD_REPORT_FILE = EVAL_DIR / "report.md"
MODEL = "gpt-4o-mini"


def load_api_key() -> str:
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key:
        return env_key

    candidate_files = [
        ROOT / ".streamlit" / "secrets.toml",
        ROOT / "Streamlit" / "secrets.toml",
    ]

    for file_path in candidate_files:
        if file_path.exists():
            with file_path.open("rb") as f:
                data = tomllib.load(f)
                key = data.get("OPENAI_API_KEY", "")
                if key:
                    return key

    return ""


def load_prompts() -> list[dict]:
    with PROMPTS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_answer(answer: str, expects: list[str]) -> dict:
    text = answer.lower()
    relevance = 5 if len(answer.strip()) > 50 else 3
    clarity = 5 if len(answer.split()) <= 220 else 3
    actionability = 5 if any(k in text for k in ["next", "step", "improve", "practice", "focus"]) else 3
    safety = 5 if all(k not in text for k in ["hate", "violent", "abuse"]) else 1

    matched = sum(1 for term in expects if term.lower().split()[0] in text)
    technical = 5 if matched >= 2 else 3

    avg = round(mean([relevance, technical, clarity, actionability, safety]), 2)
    return {
        "relevance": relevance,
        "technical_correctness": technical,
        "clarity": clarity,
        "actionability": actionability,
        "safety_tone": safety,
        "average": avg,
    }


def main() -> None:
    api_key = load_api_key()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing. Set it before running evaluation.")

    prompts = load_prompts()
    client = OpenAI(api_key=api_key, timeout=30, max_retries=2)

    results = []
    for item in prompts:
        prompt = item["prompt"]
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an HR interviewer assistant. Answer professionally and concisely."},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content or ""
        scores = score_answer(answer, item["expects"])
        results.append(
            {
                "id": item["id"],
                "category": item["category"],
                "prompt": prompt,
                "answer": answer,
                "scores": scores,
            }
        )

    averages = [r["scores"]["average"] for r in results]
    suite_avg = round(mean(averages), 2)
    pass_rate = round((sum(1 for x in averages if x >= 3.5) / len(averages)) * 100, 2)

    payload = {
        "model": MODEL,
        "total_cases": len(results),
        "suite_average": suite_avg,
        "pass_rate_percent": pass_rate,
        "pass_criteria": "Per-answer average >= 3.5",
        "results": results,
    }

    with RESULT_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    lines = [
        "# Evaluation Report",
        "",
        f"- Model: {MODEL}",
        f"- Total cases: {len(results)}",
        f"- Suite average: {suite_avg}",
        f"- Pass rate: {pass_rate}%",
        "",
        "## Cases",
    ]
    for r in results:
        lines.append(f"- {r['id']} ({r['category']}): avg={r['scores']['average']}")

    MD_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved JSON report to: {RESULT_FILE}")
    print(f"Saved Markdown report to: {MD_REPORT_FILE}")


if __name__ == "__main__":
    main()
