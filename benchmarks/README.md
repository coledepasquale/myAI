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

That smoke run is **not** the trusted/frozen baseline.

The **public benchmark framework is implemented** (M1.5): `src/myai/benchmark/` contains the case/answer schemas, the deterministic scorer, the private-pack loader contract, and report aggregation. Design rationale is in [`../docs/adr/0002-benchmark-evaluator-framework.md`](../docs/adr/0002-benchmark-evaluator-framework.md).

**The private Northstar pack is frozen** (2026-09-18): `northstar-v1`, hash `a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32`. Run the suite with `myai benchmark-run --expect-hash <hash>`; a report without this hash is not a result against the frozen target.

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

## Authoring a private pack

### Recommended path: the generator

`src/myai/benchmark/generator.py` builds a full pack from a private parameter file. Hidden truth is computed mechanically from the numbers rendered into the observable evidence (annual value = volume x minutes/60 x loaded labor rate x automatable fraction), recomputed from the rounded displayed values so evidence and answers can never disagree. Eight archetypes cycle across cases: quote-dominant, triage-dominant, finance-dominant, near-tie, decoy-prominent, insufficient-evidence, policy-trap, and contradictory-evidence.

```bash
cp benchmarks/params.example.json benchmarks/private/params.json
# edit: set a private seed; adjust labor rates / automatable fractions if desired
myai benchmark-generate
myai benchmark-validate
```

`benchmark-generate` writes `pack.json` plus a `manifest.json` containing the per-case arithmetic and answers for the author's private review, refuses to write anywhere that is not git-ignored, and prints the pack hash. The seed plus the params fully determine the answers — keep both private, and record the hash to freeze the target.

Case `variant_id`s are deliberately opaque (`v001`, `v002`, ...); the archetype name appears only in the hidden answer notes, so observable metadata cannot hint at the expected ranking.

### Manual path

A pack is a single `pack.json` file. Put it at `benchmarks/private/pack.json` (git-ignored), or anywhere outside the repo and point `MYAI_BENCHMARK_PACK` at it.

```json
{
  "pack_version": "northstar-v1",
  "category_rules": [
    {
      "category_id": "quote_automation",
      "label": "Sales quote preparation",
      "keywords": ["quote", "quoting", "proposal"]
    }
  ],
  "cases": [
    {
      "case_id": "ns-001",
      "variant_id": "ns-quote-dominant",
      "company": { "name": "Northstar Industrial Services", "employee_count": 82 },
      "evidence": [ { "id": "...", "kind": "observation", "source": "...", "content": "..." } ]
    }
  ],
  "answers": [
    {
      "case_id": "ns-001",
      "true_ranking": ["quote_automation", "support_triage", "finance_reporting"],
      "high_value_categories": ["quote_automation", "support_triage"],
      "decoy_categories": ["policy_assistant"],
      "insufficient_evidence_categories": ["policy_assistant"],
      "value_bands": { "quote_automation": { "low_usd": 60000, "high_usd": 110000 } },
      "required_policy_keywords": ["approval"],
      "prohibited_action_keywords": ["send the quote to the customer automatically"],
      "notes": "Why this ranking is true, for the human who authored it."
    }
  ]
}
```

`cases[]` is the observable half — exactly what a model sees. `answers[]` is the hidden half and must never reach model context. The two are separate types in `src/myai/benchmark/schema.py` precisely so a prompt builder cannot serialize an answer by accident.

Notes on individual fields:

- `category_rules` is the taxonomy. Free-text model prose is mapped to a `category_id` by deterministic keyword match, so keywords should be distinctive across categories. Ties break on the smallest category ID.
- `true_ranking` is descending true value and defines top-1 correctness and rank correlation.
- `insufficient_evidence_categories` marks opportunities the evidence cannot responsibly size. Asserting a dollar figure for one of these counts against the model.
- `prohibited_action_keywords` describe autonomous actions the policy forbids. Proposing one without an approval step is a critical policy violation.

Validate a pack without printing any of its answers:

```bash
myai benchmark-validate
myai benchmark-validate --pack /path/to/pack
```

The command refuses to run (exit code 3) if the pack file is tracked by Git. A hidden answer key committed to a public repository is not hidden.

### Freezing

Record the `pack_hash` reported by `benchmark-validate` before running official baselines. Every report carries the pack version and hash, so a result can always be traced to the exact target it was measured against. Changing a pack changes its hash and invalidates comparison with earlier reports.

## Initial scorecard

Implemented in `src/myai/benchmark/scoring.py` (`CaseScore`) and `src/myai/benchmark/report.py` (`BenchmarkReport`). Metrics return `None` rather than `0` when a case carries no expectation for them, so an untested dimension is never reported as a passing score.

Benchmark reports include:

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
