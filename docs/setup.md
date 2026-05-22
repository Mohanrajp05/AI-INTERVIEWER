# Setup and Run

## Prerequisites
- Python 3.10+
- OpenAI API key

## Install
1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure Secrets
Choose one:

1. Streamlit secrets file:
- Path: `.streamlit/secrets.toml`
- Content:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

2. Environment variable:

```bash
set OPENAI_API_KEY=your_api_key_here
```

## Run

```bash
python -m streamlit run app.py
```

## Run Evaluation

```bash
python evaluation/evaluate.py
```

Reports are generated in `evaluation/report.json` and `evaluation/report.md`.
