# Architecture

## Overview
The app is a single Streamlit interface with stateful interview flow, generation routed through the Portkey AI Gateway to Groq (primary) and Gemini (fallback).

## Main Components
1. UI and flow controller (`app.py`)
- Personal info intake
- Company/role selection
- Interview chat
- Feedback stage

2. Conversation state
- Stored in `st.session_state`
- Tracks setup completion, chat turns, messages, and feedback status

3. LLM service (`call_llm` in `app.py`)
- Routed through the Portkey AI Gateway (OpenAI-compatible Chat Completions API) via `client.base_url = https://api.portkey.ai/v1`
- Each provider is scoped by a Portkey virtual-key "slug"; the app holds 3 slugs each for Groq and Gemini
- Request order: try every Groq slug round-robin (`openai/gpt-oss-20b`) first; only if all Groq slugs fail does it fall back to the Gemini slugs round-robin (`gemini-3.5-flash`)
- Both model ids are overridable per-provider via `PORTKEY_GROQ_MODEL` / `PORTKEY_GEMINI_MODEL` (secrets or env) without a code change
- Slug rotation index is kept in `st.session_state.portkey_rotation` so consecutive requests spread across the 3 slugs per provider (basic client-side load balancing / rate-limit avoidance)
- Uses the memory layer (below) to bound how much context is sent
- Response cache (`st.session_state.llm_cache`): keyed by a SHA-256 hash of just the newest message's normalized text (trimmed, lowercased, whitespace-collapsed) — NOT the full conversation payload. An identical repeated message, at any point in the interview, is served from cache with zero LLM call and zero token cost; a cache-hit response is flagged in the UI ("⚡ Served from cache") and counted separately in monitoring. The cache is per-session and cleared on restart. (An earlier version keyed on the full payload including the memory window, but that shifts every turn — even a literal repeat produced a different hash and still spent tokens, so it never actually hit in practice.)

4. Monitoring
- In-session metrics:
  - request count
  - success/failure counts
  - average latency
  - prompt/completion/total token usage
  - per-provider usage count (Groq vs. Gemini), reflecting fallback activity
  - cache hit count (repeats served without spending tokens)
- Displayed in Streamlit sidebar
- Also surfaces the latest `evaluation/report.json` suite average and pass rate, if present

5. Evaluation suite (`evaluation/`)
- Prompt benchmark file (20 cases)
- Scoring rubric
- Evaluator script for pass rate and summary reports

6. Conversational memory layer (`get_memory_window` in `app.py`)
- Short-term "working memory" sent to the LLM on every chat turn: the system
  prompt plus only the last `MEMORY_WINDOW_TURNS = 3` exchanges (1 exchange =
  1 candidate answer + 1 interviewer reply, so at most 6 recent messages).
- The FULL conversation is still retained in `st.session_state.messages` and
  used in full for the end-of-interview feedback call — the memory window
  only bounds what's actively sent turn-to-turn, not what's ultimately scored.
- Purpose: keeps prompt size (and therefore cost/latency) roughly constant
  as the interview progresses, instead of growing every turn.
- The window size is a single constant (`MEMORY_WINDOW_TURNS`), easy to tune.

7. Guardrails / AI security layer (`app.py`: `is_injection_attempt`, `OFF_TOPIC_REFUSAL`)
- Layer 1 (deterministic, pre-LLM): every user message is checked against a
  regex set for jailbreak / prompt-injection / system-prompt-extraction
  phrasing ("ignore previous instructions", "reveal your system prompt",
  "act as a...", "you are now...", etc.). A match short-circuits the request
  — no LLM call is made, and the fixed refusal message is shown immediately.
  Blocked-request count is tracked in monitoring and shown in the sidebar.
- Layer 2 (prompt-level, in-LLM): the interview system prompt itself
  instructs the model to stay strictly in the interviewer role, refuse any
  request unrelated to interview prep (general knowledge, entertainment,
  unrelated coding help, etc.) with the same fixed refusal text, and never
  reveal or discuss its own instructions. This is the fallback for topic
  drift the regex layer isn't meant to catch (arbitrary off-topic questions
  can't be reliably identified by pattern matching).
- Both layers use the same canned response so behavior is consistent
  regardless of which layer caught the request.

## Data Flow
1. User submits profile info.
2. System prompt initialized from profile + target role, including the
   guardrail scope instructions.
3. User submits interview responses.
4. Each response is first checked by the deterministic guardrail filter; if
   blocked, the fixed refusal is shown and no LLM call is made.
5. Otherwise, the app sends recent conversation context through the Portkey
   gateway (Groq, falling back to Gemini on failure).
6. Assistant response is displayed and stored.
7. After turn cap, app generates final feedback the same way (Portkey → Groq → Gemini fallback).
