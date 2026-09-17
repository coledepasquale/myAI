# myAI

Experimental AI modernization platform.

The initial proof of concept tests whether a structured, evidence-grounded system can discover, justify, implement, and evaluate high-value business modernization opportunities better than a strong one-shot frontier-model baseline.

Status: foundational POC under active development.

## Local setup

Requirements: Git, Python 3.12+, and an Anthropic API key for live baseline experiments.

```bash
git clone https://github.com/coledepasquale/myAI.git
cd myAI
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

If the key is not scoped to a single Claude workspace, also set the workspace ID:

```text
ANTHROPIC_WORKSPACE_ID=wrkspc_...
```

You can find the workspace ID in Claude Console under **Settings → Workspaces**. A key created for one specific workspace does not need `ANTHROPIC_WORKSPACE_ID`.

`.env` is git-ignored. Never commit API keys.

Verify the foundation:

```bash
myai inspect northstar
ruff check .
mypy
pytest
```

## Run the one-shot baseline

The baseline gives one frontier model exactly the observable Northstar context and asks it to rank evidence-backed modernization opportunities. No Company Graph, multi-agent loop, hidden answer key, or intervention builder is involved.

Start with one paid Sonnet call:

```bash
myai baseline northstar --model claude-sonnet-5 --runs 1
```

Each call writes an immutable local artifact directory under `runs/` containing:

- `request.json` — exact model request and prompt version
- `output.json` — validated structured opportunities
- `run.json` — model, input hash, tokens, latency, estimated cost, and citation-quality metadata

`runs/` is git-ignored. Inspect the first run before executing batches. When the harness is validated, use repeated Sonnet runs for development and Claude Opus 5 for the frozen strong-control benchmark.

See `POC_CHARTER.md` for the experiment design and `docs/` for founder/market context.
