# Benchmarks

The benchmark layer measures whether myAI is actually better than a strong frontier-model baseline rather than merely more complicated.

## Public vs private benchmark material

This repository is public. Therefore **real hidden benchmark truth must never be committed here**.

Public benchmark code may define:

- schemas for benchmark cases;
- evaluator interfaces;
- scoring logic that does not reveal answers;
- toy/example cases;
- tooling for loading local or CI-injected private benchmark packs;
- report aggregation and visualization logic;
- validation that a benchmark pack is complete/versioned.

Private benchmark material belongs under `benchmarks/private/` (gitignored) or in a separate private repository / secure artifact store. It may contain:

- true opportunity rankings;
- hidden workflow costs and frequencies;
- policy edge cases;
- intervention acceptance cases;
- adversarial/contradictory evidence cases;
- randomized fixture seeds not exposed to the runtime agent;
- decoy opportunity labels;
- allowed/forbidden intervention classes;
- value ranges and confidence expectations.

## Why this boundary matters

If development agents can read the benchmark answers, the experiment is contaminated: the system may appear to reason correctly while simply encoding the expected results. The runtime system must see only the same observable company evidence that the baseline receives.

The first real benchmark pack must be created and frozen **before** implementing the structured opportunity engine and before collecting a large set of official Opus/Fable answers, so later architectural work is evaluated against a fixed target rather than a moving test.

## Current status — 2026-09-17

The live baseline harness is working end to end. One Sonnet 5 smoke run succeeded and is documented in `docs/experiments/2026-09-17-sonnet-baseline-smoke.md`.

That smoke run is **not** the trusted/frozen baseline because no private evaluator exists yet.

The immediate next milestone is therefore the benchmark/evaluator freeze.

## Recommended first benchmark design

Create a family of controlled Northstar cases rather than repeatedly calling the exact same eight-record fixture.

Useful case variations should include:

- quote automation genuinely highest-value;
- support triage genuinely highest-value;
- finance reporting as a clear but smaller win;
- an attractive-looking low-value decoy;
- insufficient evidence for a numeric ROI;
- a policy constraint that makes an otherwise attractive autonomous intervention unsafe;
- contradictory evidence that should reduce confidence;
- volume/cost changes that alter the correct ranking;
- cases where “do not automate” is a valid conclusion.

The runtime/baseline sees only the observable variant. The private evaluator sees the hidden generation parameters and answer truth.

## Suggested private case fields

The exact schema is still to be implemented, but a private benchmark case should be able to represent:

- `case_id`
- `fixture_variant_id`
- hidden opportunity classes
- expected top opportunity / acceptable rank bands
- hidden annual-value ranges
- hidden labor/cycle-time inputs
- known decoys
- critical policies/constraints
- prohibited autonomous actions
- acceptable intervention classes
- ambiguity / “insufficient evidence” expectations
- hidden seed/generator metadata

The public evaluator should consume an opaque/private pack through an interface; it should not require the answers to be committed alongside code.

## Initial scorecard

At minimum, benchmark reports should include:

- top-1 opportunity correctness;
- top-3 recall of true high-value opportunities;
- ranking correlation with hidden value/order;
- evidence citation validity;
- evidence support / factual-grounding rate;
- unsupported claim rate;
- unsupported numeric ROI rate;
- ROI calibration error or expected-range coverage;
- policy-risk detection;
- critical policy violations;
- confidence calibration;
- run-to-run stability where repeated runs are used;
- model/provider/prompt/input hash;
- token usage;
- latency;
- cost.

Later intervention benchmarks should add deterministic acceptance rate, regressions, safety failures, and business-proxy deltas.

## Model roles for the frozen baseline

Planned roles as of 2026-09-17:

- `claude-sonnet-5` — development/reference baseline.
- `claude-opus-5` — **primary strong official one-shot baseline**.
- `claude-fable-5-1` — **frontier ceiling / stress test**.

The structured system should not be declared successful merely because it beats Sonnet. It should materially improve on Opus under the same observable context, and its relationship to the Fable ceiling should be explicitly reported.

Before the frozen runs, make reasoning/effort configuration explicit and include it in run metadata rather than relying on provider defaults.

## Suggested first official suite

After the private pack is frozen:

1. Run roughly 20 **distinct** Northstar benchmark cases with Sonnet for reference.
2. Run the same cases with Opus as the primary control.
3. Run the same cases with Fable as a frontier ceiling/stress test.
4. Repeat selected ambiguous cases if model variance needs measurement.
5. Freeze/report those results before implementing the Company Model/opportunity engine.

The purpose is not to maximize the number of API calls. It is to establish a trustworthy, reproducible control that the proposed architecture must beat.

See `docs/PROJECT_STATE.md` for the complete continuation plan.
