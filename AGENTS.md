# Agent / LLM continuation instructions

This repository is designed to be continued across coding-agent and LLM sessions without relying on chat history.

## Read this first

Before changing code or proposing architecture, read these files in order:

1. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — canonical current state, experiment history, decisions, exact next steps, and stop conditions.
2. [`POC_CHARTER.md`](POC_CHARTER.md) — governing hypothesis, design principles, kill criteria, and milestones.
3. [`docs/founder-one-pager.md`](docs/founder-one-pager.md) — concise product thesis and differentiation.
4. [`docs/research/market-landscape.md`](docs/research/market-landscape.md) — market and competitor research that motivated the POC.
5. [`benchmarks/README.md`](benchmarks/README.md) — benchmark-integrity rules and public/private boundary.
6. [`docs/adr/`](docs/adr/) — accepted architectural decisions, including [`0002`](docs/adr/0002-benchmark-evaluator-framework.md) on why the evaluator is deterministic and why answers live outside this repo.

Treat `docs/PROJECT_STATE.md` as the authoritative handoff for what has already happened and what should happen next. If another document appears to conflict with it on sequencing, prefer `PROJECT_STATE.md` unless the conflict has been deliberately resolved in a newer ADR or commit.

## Current state in one paragraph

As of 2026-09-17, M0 foundation, the M1 live Anthropic baseline harness, and the M1.5 public benchmark/evaluator framework are implemented. A single successful `claude-sonnet-5` smoke run against Northstar has proven the experiment plumbing end to end. That run is **not** the frozen benchmark. The public framework that scores model output against hidden truth now exists in `src/myai/benchmark/`, but **no private answer key has been authored yet**. The immediate next step is to author and freeze the private Northstar benchmark pack and its randomized cases (`docs/PROJECT_STATE.md` §12 Step 3) **before** collecting more model outputs or implementing the Company Model/opportunity engine. Opus 5 is planned as the primary strong baseline; Fable 5.1 is planned as a frontier ceiling/stress test; Sonnet 5 remains a development/reference baseline.

## Non-negotiable guardrails

- This repository is public. Never commit API keys, workspace IDs that should remain private, customer data, or real hidden benchmark answers.
- `.env`, `runs/`, `artifacts/`, and `benchmarks/private/` are intentionally git-ignored.
- Never add hidden benchmark truth to normal model/runtime context. `BenchmarkCase` (observable) and `CaseAnswerKey` (hidden) are separate types for this reason; never merge them for convenience.
- Sessions that build or tune the structured myAI system must consume benchmark results at the **aggregate report level only**. Do not read per-case score files under `runs/benchmark_*/` (`*.score.json`) and do not run `benchmark-run --show-scores` in a context a coding agent can read: per-case hits/misses combined with stored outputs reveal individual hidden answers.
- Do not make live Anthropic calls in CI. CI must remain deterministic and credential-free.
- Do not train or fine-tune a model merely because it is technically possible. Training requires a measured repeatable gap and enough labeled trajectories.
- Do not add a database, graph database, agent framework, polished UI, or production deployment layer unless the current experiment creates a concrete need.
- Do not implement multi-agent complexity before the strong one-shot baseline and evaluator are frozen.
- Do not interpret LLM-generated ROI numbers as ground truth unless the hidden benchmark/evaluator supports them.
- High-impact future production actions involving money, external communication, deletion, permissions, or commitments require explicit human approval. The POC remains sandbox-first.

## Development style

Prefer small, falsifiable increments. Keep provider-specific behavior behind `StructuredModel`. Keep evidence IDs, assumptions, provenance, run metadata, and deterministic evaluation first-class. Every new layer must earn its complexity against the same benchmark rather than moving the target.

When resuming in a new session, do not ask the user to restate project history until you have read the files above.
