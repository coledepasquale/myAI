# 2026-09-18 — Official Sonnet 5 reference baseline (frozen pack)

First full suite against the frozen target. This is the **development/reference
baseline**; Opus 5 (primary strong control) and Fable 5.1 (frontier ceiling)
are still pending.

- **Model:** `claude-sonnet-5`, effort `high`, adaptive thinking (explicit)
- **Pack:** `northstar-v1`, hash `a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32`
- **Scorer:** `scorer-v0.2`
- **Cases:** 20/20 succeeded, no failures
- **Run dir (local):** `runs/benchmark_20260918T123839Z_3494f233_claude-sonnet-5`
- **Cost:** $1.12 (64,648 in / 99,001 out tokens); ~$0.056/case; ~13 min wall clock for the suite

## Aggregate results

| Metric | Value |
|---|---:|
| Top-1 accuracy | 75% |
| Top-3 recall | 95% |
| Unmatched opportunity rate | 0% |
| Rank correlation (Spearman) | 0.919 |
| Evidence citation validity | 100% (0 fabricated IDs) |
| Decoy promoted into top-3 | 0% |
| Unsupported ROI rate | 11% |
| ROI band coverage (±35%) | 88% |
| ROI calibration error | 0.180 |
| Policy detection | 100% |
| Critical policy violations | 0 |
| Confidence Brier | 0.213 |
| Top-1 stability | n/a (single run per case) |

An offline `myai benchmark-rescore` of the stored outputs reproduced every
score exactly, verifying deterministic rescoring end to end on real data.

## Interpretation (aggregate level only)

What went **well for the baseline** — one-shot Sonnet with good context is
already strong on this task family:

- Perfect evidence discipline: zero fabricated citation IDs across ~97
  opportunities. Grounding alone is not a differentiator against frontier
  one-shot prompting.
- Decoys never cracked the top-3, and no proposal violated the approval policy.
- Rank correlation 0.919: the overall ordering is largely right.

Where the baseline **leaves room** — candidate value for the structured system:

- **Top-1 accuracy 75%:** one case in four picks the wrong single best
  opportunity, the headline decision a customer would act on.
- **Unsupported ROI 11%:** the model still asserts dollar figures where the
  evidence cannot responsibly support a number.
- **ROI calibration 0.180 / coverage 88%:** value estimates average 18% off the
  band midpoint; 12% fall outside the defensible range entirely.
- **Confidence Brier 0.213:** stated confidence only loosely tracks whether an
  opportunity is truly high-value.

The matcher tripwire (unmatched rate 0%) means these numbers are model
behavior, not scoring artifacts. Caveat: aggregate matching cannot detect an
opportunity matched to the *wrong* category; the per-case audit, if wanted,
belongs to the pack author, not to build sessions (see AGENTS.md).

## What this does not yet establish

Sonnet is the reference, not the control. The structured system's bar is Opus 5
on the same 20 cases, with Fable 5.1 as the capability ceiling. No conclusion
about the startup thesis is justified until those runs exist.
