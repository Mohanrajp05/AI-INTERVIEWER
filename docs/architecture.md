# Architecture

## Overview
The app is a single Streamlit interface with stateful interview flow and OpenAI-backed generation.

## Main Components
1. UI and flow controller (`app.py`)
- Personal info intake
- Company/role selection
- Interview chat
- Feedback stage

2. Conversation state
- Stored in `st.session_state`
- Tracks setup completion, chat turns, messages, and feedback status

3. LLM service
- OpenAI Chat Completions API
- Uses bounded context window to control prompt size
- Retry handling for connection errors

4. Monitoring
- In-session metrics:
  - request count
  - success/failure counts
  - average latency
  - prompt/completion/total token usage
- Displayed in Streamlit sidebar

5. Evaluation suite (`evaluation/`)
- Prompt benchmark file (20 cases)
- Scoring rubric
- Evaluator script for pass rate and summary reports

## Data Flow
1. User submits profile info.
2. System prompt initialized from profile + target role.
3. User submits interview responses.
4. App sends recent conversation context to OpenAI.
5. Assistant response is displayed and stored.
6. After turn cap, app generates final feedback.
