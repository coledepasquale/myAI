# 2026-09-18 — Official frozen baseline report (Sonnet 5 / Opus 5 / Fable 5.1)

All three official one-shot suites ran against the frozen pack on 2026-09-18.
This is the control record the structured myAI system must beat.

- **Pack:** `northstar-v1`, hash `a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32`
- **Scorer:** `scorer-v0.2` | **Prompt:** baseline-v0.1 (frozen) | **Effort:** `high`, adaptive thinking, explicit
- **Runs:** 20 distinct cases x 1 run per model; 20/20 succeeded for every model
- **Run dirs (local):** `benchmark_20260918T123839Z_3494f233_claude-sonnet-5`,
  `benchmark_20260918T130102Z_5b48d7bf_claude-opus-5`,
  `benchmark_20260918T143503Z_0adc1ae6_claude-fable-5-1`
- Note: one Fable attempt was interrupted (Ctrl-C after 11 cases) and one crashed on a
  full disk before any case completed; both partial run dirs were deleted and the
  clean 20/20 rerun above is the official record. The disk-full crash motivated the
  best-effort artifact persistence fix in the runner.

## Results

| Metric | Sonnet 5 | Opus 5 | Fable 5.1 |
|---|---:|---:|---:|
| Top-1 accuracy | 75% | **95%** | 85% |
| Top-3 recall | 95% | **100%** | 92% |
| Unmatched opportunity rate | 0% | 0% | 0% |
| Rank correlation | 0.919 | **0.975** | 0.969 |
| Evidence citation validity | 100% | 100% | 100% |
| Fabricated evidence IDs | 0 | 0 | 0 |
| Decoy in top-3 | 0% | 0% | 2% |
| Unsupported ROI rate | 11% | 26% | **5%** |
| ROI band coverage (±35%) | **88%** | 73% | 78% |
| ROI calibration error | **0.180** | 0.568 | 0.329 |
| Policy detection | 100% | 100% | 100% |
| Critical policy violations | 0 | 0 | 0 |
| Confidence Brier | **0.213** | 0.285 | 0.252 |
| Suite cost | $1.12 | $2.92 | $4.55 |
| Output tokens | 99,001 | 103,932 | 78,003 |

## Headline findings

1. **Discovery and ranking are near-ceiling for one-shot Opus.** 95% top-1 /
   100% top-3 / rho 0.975 leaves at most one case in twenty of headroom on this
   pack. Per the charter's falsification rule, structured architecture cannot be
   justified by discovery improvement on this task family.
2. **Grounding and safety are commodity.** Zero fabricated evidence IDs, zero
   critical policy violations, near-zero decoy promotion for all three models.
3. **The value axis is open and no model dominates it.** Sonnet is the best
   calibrated but weakest at discovery; Opus is the best discoverer but the most
   willing to assert unsupported ROI (26%) and the furthest off on values
   (calibration 0.568); Fable is the most epistemically disciplined (5%
   unsupported) but not the best calibrated. The best single-model profile does
   not exist; calibrated valuation with disciplined abstention is the only
   dimension with meaningful headroom.
4. **More capability does not monotonically help.** Fable trails Opus on top-1
   (85% vs 95% — within single-run noise on n=20, see caveats) while beating
   everyone on abstention discipline.

## Decisiveness caveats (recorded honestly)

- **n=20, single run per model.** 95% vs 85% top-1 is 19/20 vs 17/20; the
  ~two-case difference is within binomial noise. Model-vs-model ordering on
  discovery metrics is NOT settled; stability was not measured (repeat=1).
- **The pack's truth is generated arithmetic** (volume x minutes x rate x
  automatable fraction) rendered into evidence. That makes truth computable from
  the observable numbers, which favors careful one-shot arithmetic and likely
  inflates discovery scores relative to messy real-world evidence. Conclusions
  about discovery being "solved" hold for this world; they are weaker evidence
  about noisier ones.
- **ROI calibration partially measures assumption mismatch, not epistemic
  failure.** Models were not told the pack's automatable fractions or loaded
  rates; a model assuming 50% automatable where the pack assumes 80% scores
  "miscalibrated" despite defensible reasoning. The unsupported-ROI rate is the
  cleaner epistemic signal (asserting numbers where volume/time data is absent),
  and Opus's 26% there is a real finding.
- **All three baselines are Claude-family.** No cross-provider control was run.
- **What is decisive:** the pack was frozen (hash recorded) before any model
  output was collected, the scorer is deterministic, the matcher tripwire read
  0% for all models, and offline rescoring reproduces every number. Within its
  synthetic world, this comparison is clean.

## Implications for the next experiment

The cheapest way the remaining gap could die is prompt-level: a baseline-v0.2
one-shot prompt with an explicit abstention policy and assumption-disclosure
requirements might close the unsupported-ROI and calibration gaps without any
structured system. That experiment must run BEFORE building the Company Model:
if a paragraph of prompt closes the value gap, the kill gate applies to the
architecture thesis on this benchmark. See PROJECT_STATE §12 for sequencing.
