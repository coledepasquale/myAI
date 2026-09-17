# 2026-09-17 — First live Sonnet baseline smoke test

This document records the first successful end-to-end paid baseline call against the public Northstar fixture. It is a **smoke test of the experiment harness**, not the frozen benchmark result.

## Goal

Verify that the M1 path works end to end:

```text
Northstar observable context
    ↓
baseline-v0.1 request
    ↓
Anthropic structured-output adapter
    ↓
Claude Sonnet 5
    ↓
validated BaselineOutput
    ↓
local immutable run artifacts
```

No Company Model, multi-agent reasoning, hidden answer key, intervention builder, or sandbox evaluator was used.

## First attempt

Command:

```bash
myai baseline northstar --model claude-sonnet-5 --runs 1
```

The request failed with HTTP 400. Anthropic reported that the API key was not scoped to a workspace and required the `anthropic-workspace-id` header.

This was an integration/configuration issue, not a model-quality result. No model output was produced.

### Fix

PR #3 added optional local configuration:

```text
ANTHROPIC_WORKSPACE_ID=wrkspc_...
```

The Anthropic adapter now sends `anthropic-workspace-id` only when that local value is configured. Keys already scoped to a single workspace do not require it.

## Successful run

Command:

```bash
myai baseline northstar --model claude-sonnet-5 --runs 1
```

Local artifact directory from the executing machine:

```text
runs/20260917T201333Z_6f176fc5-11b4-48f5-a11e-03c69086d149
```

The raw directory is intentionally git-ignored, so this Markdown record is the durable repository summary.

### Ranked opportunities

| Rank | Opportunity | Value/yr | Confidence | Feasibility | Evidence IDs (short) |
|---|---|---:|---:|---:|---|
| 1 | Automate Sales Quote Generation and Approval Routing | $15,000 | 55% | 70% | 11111111, 22222222, 33333333 |
| 2 | Automate Weekly Finance Operations Report | $9,500 | 60% | 80% | 66666666 |
| 3 | Automate Routine Support Ticket Triage | $8,000 | 50% | 75% | 44444444, 55555555 |
| 4 | Deploy Self-Service Policy Assistant (Pilot, Value Unconfirmed) | — | 30% | 60% | 88888888 |

### Run metadata

- model: `claude-sonnet-5`
- input tokens: 3,105
- output tokens: 4,881
- latency: 51,652 ms
- estimated cost: $0.0550
- invalid evidence IDs: 0

## What was encouraging

- The model found the seeded quote, finance-reporting, support-triage, and policy-search opportunity classes without being told the hidden expected ranking.
- Quote automation cited workflow, volume, and approval-policy evidence rather than only one observation.
- The policy assistant was marked “value unconfirmed” rather than assigning a confident ROI despite weak direct value evidence.
- All cited evidence IDs existed in the observable fixture.
- Structured output and artifact persistence worked.

## What this run does not establish

The generated annual values are not ground truth. Northstar does not currently expose enough labor-cost, downstream-revenue, automation-rate, or implementation-cost truth for a one-shot model to know those numbers precisely.

Likewise, the observed order is plausible but is not yet scored against a frozen private evaluator.

Therefore this run should not be quoted as “the baseline accuracy” or as evidence that quote automation truly creates $15K/year.

## Decision after this run

Do **not** immediately collect many more identical Sonnet/Opus/Fable outputs.

The next step is to freeze the private benchmark/evaluator and create controlled randomized Northstar variants first. This prevents later model outputs from influencing how correctness is defined.

Planned model roles after the evaluator is frozen:

- Sonnet 5 — development/reference baseline.
- Opus 5 — primary strong official baseline.
- Fable 5.1 — frontier ceiling / stress test.

See [`../PROJECT_STATE.md`](../PROJECT_STATE.md) and [`../../benchmarks/README.md`](../../benchmarks/README.md) for the continuation plan.
