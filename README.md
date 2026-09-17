# myAI

Experimental evidence-grounded AI modernization platform.

The POC tests whether a structured system can understand how a company works, identify and justify high-value AI/software improvements, and eventually build/evaluate those interventions **materially better than a strong one-shot frontier-model baseline given the same observable context**.

## Current status — 2026-09-17

- M0 foundation: **complete**.
- M1 Anthropic baseline runner: **complete**.
- First successful Sonnet 5 end-to-end smoke run: **complete**.
- Official trusted baseline: **not frozen yet**.
- Immediate next step: **build and freeze the private benchmark/evaluator and randomized Northstar cases before collecting more official model outputs or building the Company Model.**

### New LLM / coding-agent session

Start with:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)
3. [`POC_CHARTER.md`](POC_CHARTER.md)

`docs/PROJECT_STATE.md` is the canonical continuation handoff: project history, market conclusions, merged work, experiment results, current interpretation, model strategy, and exact next implementation sequence.

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

Put secrets only in local `.env`:

```text
ANTHROPIC_API_KEY=your_key_here
```

If the key is not scoped to a single Claude workspace, also set:

```text
ANTHROPIC_WORKSPACE_ID=wrkspc_...
```

The workspace ID is available in Claude Console under **Settings → Workspaces**. A key created for one specific workspace does not need `ANTHROPIC_WORKSPACE_ID`.

`.env` is git-ignored. Never commit API keys.

Verify the checkout:

```bash
myai inspect northstar
ruff check .
mypy
pytest
```

## Baseline runner

The one-shot control gives a frontier model exactly the observable Northstar company context and asks it to rank evidence-backed modernization opportunities. No Company Graph, multi-agent loop, hidden answer key, or intervention builder is involved.

A paid smoke call can be run with:

```bash
myai baseline northstar --model claude-sonnet-5 --runs 1
```

Each successful call creates a local git-ignored directory under `runs/` containing:

- `request.json` — exact request and prompt version;
- `output.json` — validated structured opportunities;
- `run.json` — provider/model, input hash, tokens, latency, estimated cost, and citation-validity metadata.

The first successful smoke run is documented in [`docs/experiments/2026-09-17-sonnet-baseline-smoke.md`](docs/experiments/2026-09-17-sonnet-baseline-smoke.md).

**Do not treat that Sonnet result as the frozen benchmark and do not run a large Opus/Fable batch yet.** The benchmark/evaluator must be defined and frozen first so the target is not influenced by model outputs.

## Documentation

- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — canonical current-state/continuation document.
- [`POC_CHARTER.md`](POC_CHARTER.md) — experimental hypothesis, principles, kill criteria, milestones.
- [`docs/founder-one-pager.md`](docs/founder-one-pager.md) — product thesis for humans.
- [`docs/research/market-landscape.md`](docs/research/market-landscape.md) — research/competitive landscape.
- [`benchmarks/README.md`](benchmarks/README.md) — public/private benchmark boundary and next benchmark design.
- [`docs/adr/`](docs/adr/) — architecture decisions.

This repository is public. Hidden benchmark truth, credentials, and future sensitive customer data must remain outside committed runtime-visible files.
