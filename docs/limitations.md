# Known Limitations

1. Evaluation scoring is heuristic
- Current evaluator uses lightweight rule-based scoring and is not a perfect quality metric.

2. No persistent database
- Chat history is session-scoped and resets on reload.

3. Model output variance
- Responses can vary across calls due to LLM nondeterminism.

4. Basic monitoring only
- Metrics are in-session and not exported to an external observability stack.

5. Cost and latency sensitivity
- API latency and token usage depend on prompt length and model availability.

6. No authentication/rate limiting
- Not production-hardened for public multi-user deployment.
