# Interview Chatbot (Streamlit)

AI-powered interview simulator that asks role-specific questions and provides end-of-session feedback.

## Features
- Candidate setup flow (name, experience, skills, target role, company)
- Multi-turn interview chat powered by OpenAI
- Configurable chat turn cap and context window
- End-of-interview scoring and feedback
- Basic monitoring: request count, success rate, latency, token usage
- Evaluation suite with benchmark prompts and pass-rate reporting

## Tech Stack
- Python
- Streamlit
- OpenAI API

## Quick Start
1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Set API key (either method):
   - Streamlit secrets: `.streamlit/secrets.toml` with `OPENAI_API_KEY="..."`
   - Environment variable: `OPENAI_API_KEY=...`
4. Run app:
   - `python -m streamlit run app.py`

## Evaluation
- Benchmark prompts: `evaluation/benchmark_prompts.json`
- Rubric: `evaluation/rubric.md`
- Run evaluator:
  - `python evaluation/evaluate.py`
- Output reports:
  - `evaluation/report.json`
  - `evaluation/report.md`

## Current Results
- Model: `gpt-4o-mini`
- Total benchmark cases: `20`
- Suite average score: `4.56 / 5`
- Pass rate: `100.0%`
- Pass criteria: `Per-answer average >= 3.5`

## Project Docs
- Setup and run: `docs/setup.md`
- Architecture: `docs/architecture.md`
- Known limitations: `docs/limitations.md`

