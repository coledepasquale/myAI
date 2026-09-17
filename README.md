# myAI

Experimental AI modernization platform.

The initial proof of concept tests whether a structured, evidence-grounded system can discover, justify, implement, and evaluate high-value business modernization opportunities better than a strong one-shot frontier-model baseline.

Status: foundational POC under active development.

## Local setup

Requirements: Git, Python 3.12+, and an Anthropic API key for live baseline experiments.

```bash
git clone https://github.com/coledepasquale/myAI.git
cd myAI
git switch foundation-v0.1
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
```

Put your key only in the local `.env` file:

```text
ANTHROPIC_API_KEY=your_key_here
```

`.env` is git-ignored. Never commit API keys.

Verify the current foundation:

```bash
myai inspect northstar
ruff check .
mypy
pytest
```

See `POC_CHARTER.md` for the experiment design and `docs/` for founder/market context.
