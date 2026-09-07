# Known Limitations

1. Evaluation scoring is heuristic
- Current evaluator uses lightweight rule-based scoring and is not a perfect quality metric.

2. No persistent database
- Chat history is session-scoped and resets on reload.

3. Model output variance
- Responses can vary across calls due to LLM nondeterminism, and additionally because a request may be served by either Groq (`openai/gpt-oss-20b`) or, on fallback, Gemini (`gemini-3.5-flash`) — different underlying models with different response styles.

4. Basic monitoring only
- Metrics are in-session and not exported to an external observability stack.

5. Cost and latency sensitivity
- API latency and token usage depend on prompt length and model availability.

6. No authentication/rate limiting
- Not production-hardened for public multi-user deployment.

7. Evaluation suite targets a different backend
- `evaluation/evaluate.py` still calls OpenAI (`gpt-4o-mini`) directly and does not go through the Portkey/Groq/Gemini path the live app uses, so its scores are not a direct measure of production behavior.

8. Slug rotation is a simple in-session counter
- Round-robin across each provider's Portkey virtual-key slugs resets per Streamlit session (not shared/coordinated across users or app restarts).

9. Guardrails are heuristic, not a hard security boundary
- The deterministic pre-LLM filter (`is_injection_attempt`) matches a curated set of known jailbreak/injection phrasings via regex — it will not catch every possible attack phrasing, only the common ones.
- General off-topic drift (e.g. an unrelated trivia question) that doesn't match the injection patterns relies entirely on the LLM honoring the system prompt's scope rules, which is a best-effort control, not a guarantee — a sufficiently adversarial prompt could still get a capable model to break character.
- There is no output-side filtering: if the model does produce an off-topic or leaked-instruction response despite the guardrails, it is shown to the user as-is.

10. Response cache is exact-text-match and in-memory only
- `st.session_state.llm_cache` is keyed on just the newest message's normalized text (trimmed/lowercased/whitespace-collapsed) — a rephrased repeat of the same question is treated as new and still costs tokens.
- Because it ignores conversation context, the same wording (e.g. "yes", "can you repeat that") asked at two different points in the interview is treated as the same cache entry and reuses the earlier answer — this is a deliberate trade-off to actually catch literal repeats (keying on the full context instead meant a repeat almost never hit, since the memory window shifts every turn), but it means a cache hit is not always contextually correct.
- The cache is per-session and unbounded for the session's lifetime; it is cleared on restart/reload and never shared across users, so it does not reduce cost across a full deployment, only within one candidate's single run.

11. Memory window is short and fixed
- `MEMORY_WINDOW_TURNS = 3` means the model only actively "remembers" the last 3 exchanges when generating its next question — anything the candidate said earlier than that has left the live context, so the interviewer can lose track of details mentioned much earlier (though the full transcript is still used for the final feedback score, since that's built from the complete history, not the windowed one).
- The window size is a fixed constant, not adaptive to conversation content or length.
