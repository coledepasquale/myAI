# myAI documentation

This directory keeps the product thesis, market research, experiment history, architectural decisions, and continuation context close to the code.

## Start here

- [`PROJECT_STATE.md`](./PROJECT_STATE.md) — **canonical continuation handoff**. Read this first in a new LLM/coding session. It explains the project evolution, current implementation, experiment history, what has and has not been proven, model strategy, and exact next steps.
- [`founder-one-pager.md`](./founder-one-pager.md) — concise human handoff: what we believe, what we are building, why now, and what would falsify the idea.
- [`research/market-landscape.md`](./research/market-landscape.md) — market/competitor research and implications for the POC.
- [`experiments/2026-09-17-sonnet-baseline-smoke.md`](./experiments/2026-09-17-sonnet-baseline-smoke.md) — first successful live baseline smoke test and its correct interpretation.
- [`../POC_CHARTER.md`](../POC_CHARTER.md) — governing experimental charter and kill criteria.
- [`../benchmarks/README.md`](../benchmarks/README.md) — benchmark integrity, private answer-key boundary, and current evaluator plan.
- [`adr/`](./adr/) — architectural decision records.

## Current milestone

M0 foundation and the M1 live Anthropic baseline runner are implemented. One Sonnet 5 smoke run has succeeded. The next milestone is to **freeze the evaluator/private Northstar benchmark and randomized cases before collecting official Opus/Fable baseline batches or implementing the structured Company Model/opportunity engine**.

## Documentation rule

Research findings inform the product thesis, but the POC is not allowed to encode competitor marketing claims or hidden benchmark answers as implementation assumptions. Claims that affect architecture should be promoted into an ADR with a clear decision and revisit condition.

This repository is public. Secrets, sensitive data, and real hidden benchmark truth must not be committed here.
