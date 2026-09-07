# Setup and Run

## Prerequisites
- Python 3.10+
- A [Portkey](https://portkey.ai/) account with Groq and/or Gemini virtual keys configured

## Install
1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure Secrets
The app talks to Groq and Gemini through the Portkey AI Gateway (no direct
OpenAI key needed). Requests try each Groq virtual key round-robin first;
if all Groq slugs fail, it falls back to the Gemini virtual keys the same
way. Choose one:

1. Streamlit secrets file:
- Path: `.streamlit/secrets.toml`
- Content:

```toml
PORTKEY_API_KEY = "your_portkey_api_key"
PORTKEY_GROQ_SLUGS = ["groq-virtual-key-1", "groq-virtual-key-2", "groq-virtual-key-3"]
PORTKEY_GEMINI_SLUGS = ["gemini-virtual-key-1", "gemini-virtual-key-2", "gemini-virtual-key-3"]
```

2. Environment variables (comma-separated slug lists):

```bash
set PORTKEY_API_KEY=your_portkey_api_key
set PORTKEY_GROQ_SLUGS=groq-virtual-key-1,groq-virtual-key-2,groq-virtual-key-3
set PORTKEY_GEMINI_SLUGS=gemini-virtual-key-1,gemini-virtual-key-2,gemini-virtual-key-3
```

You only need slugs for the provider(s) you actually use — leaving one
provider's slug list empty just skips it.

## Run

```bash
python -m streamlit run app.py
```

## Run Evaluation

```bash
python evaluation/evaluate.py
```

Reports are generated in `evaluation/report.json` and `evaluation/report.md`.
