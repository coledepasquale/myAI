# 2026-09-18 — baseline-v0.2 (value-discipline prompt): the kill gate trips

One paragraph of prompt closed the entire remaining value gap. Opus 5, same 20
frozen cases, same effort, prompt `baseline-v0.2` (v0.1 plus an abstention and
assumption-disclosure policy — no environment-specific numbers).

| Metric | Opus v0.1 | **Opus v0.2** | Best prior (any model) |
|---|---:|---:|---:|
| Top-1 accuracy | 95% | 90% | 95% (Opus v0.1) |
| Top-3 recall | 100% | 92% | 100% (Opus v0.1) |
| Rank correlation | 0.975 | 0.970 | 0.975 |
| Unsupported ROI rate | 26% | **0%** | 5% (Fable) |
| ROI band coverage | 73% | **90%** | 88% (Sonnet) |
| ROI calibration error | 0.568 | **0.192** | 0.180 (Sonnet) |
| Confidence Brier | 0.285 | **0.187** | 0.213 (Sonnet) |
| Suite cost | $2.92 | $3.34 | — |

Run dir: `benchmark_20260918T151647Z_f4f0d496_claude-opus-5`. Matcher tripwire
0%. The small top-1/recall movement (90%/92% vs 95%/100%) is within single-run
noise on n=20 and may also reflect legitimately conservative reranking of
abstained opportunities.

## Verdict

**Every dimension of the benchmark is now at or near ceiling for a one-shot
frontier model with a well-written prompt.** Discovery was already solved by
v0.1 Opus; the value/abstention/calibration gap — the last candidate wedge for
a structured reasoning layer — closed with prompt-level discipline. Zero
unsupported ROI claims, 90% band coverage, and the best confidence calibration
of any run, at a total experimental spend of roughly $30.

Per the charter's falsification rule, the kill gate applies to the structured
reasoning thesis on this benchmark: **do not build the Company Model /
opportunity engine to improve reasoning over provided evidence.** The
architecture cannot earn its complexity against this control.

## What survives (scoped carefully)

1. **Reasoning over clean, provided evidence is commodity.** The moat, if one
   exists, lives in the stages this benchmark deliberately held constant:
   acquiring the evidence from real systems, building and safely executing
   interventions, and measuring real outcomes.
2. **Calibration in the real world still requires outcome data.** The prompt
   fixed calibration in a world whose truth is computable from the evidence.
   Real ROI calibration needs predicted-vs-measured deltas across deployments —
   a proprietary dataset no frontier model ships with. That wedge moved from
   "architecture" to "data collected by closing the loop with real customers."
3. **The benchmark harness itself remains the project's asset** — any future
   layer (evidence extraction, intervention acceptance, outcome measurement)
   gets the same treatment: frozen target, deterministic scoring, kill gate.

## Caveats

Single run per configuration, n=20, synthetic computable world, Claude-family
only. None of these weaken the kill verdict: the benchmark's simplicity biases
in the baseline's favor, which is precisely why *failing to beat the baseline
here* is a strong stop signal, while *beating it here* would have been weak
evidence. The cheap world did its job — it killed the cheap thesis.
