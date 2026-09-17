# ADR 0002 — Benchmark/evaluator framework

Status: accepted for POC v0.1 (M1.5)

## Context

`docs/PROJECT_STATE.md` §11 requires the benchmark and evaluator to be built **before** large frontier-model batches are collected and before the structured Company Model is implemented. The risk is experimental contamination: if many model answers are read first, the evaluator drifts toward whatever the models happened to say, and the comparison stops being falsifiable.

Two constraints shape the design:

1. The repository is public, so real answer keys cannot live here.
2. A stored run artifact must rescore identically months later, or "myAI beats the baseline" is not a reproducible claim.

## Decision

**Split the observable half from the hidden half at the type level.** `BenchmarkCase` carries only what a model may see (company metadata, evidence). `CaseAnswerKey` carries hidden truth. They are separate Pydantic models rather than one model with private fields, so serializing a case into a prompt cannot leak answers even by accident.

**Ship public scoring code, load private data.** The repo contains schemas, scoring, aggregation, and a `BenchmarkPackLoader` contract. Real packs load from the git-ignored `benchmarks/private/`, or from `MYAI_BENCHMARK_PACK` for a pack kept in a private repository or artifact store. A committed toy pack exercises the code in tests.

**Classify opportunities with deterministic keyword rules, not an LLM judge.** Scoring an output against a category taxonomy needs free-text prose mapped to a category ID. An LLM judge would be more flexible but non-reproducible, differently biased per model generation, and itself a confound in an experiment about model capability. Keyword rules are transparent, cheap, and stable. Ties break on the lexicographically smallest category ID so a given output always scores identically.

**Keep the taxonomy in pack data, not in code.** Category rules ship inside the pack. Public scoring logic stays environment-neutral and no Northstar-specific taxonomy is committed.

**Version and hash every pack.** `BenchmarkPack.pack_hash` is a SHA-256 over canonical JSON, and every report is stamped with the pack version and hash. A score that cannot be traced to a frozen target is not a benchmark result.

**Distinguish "not applicable" from zero.** Metrics return `None` when a case carries no expectation for them (no policy keywords, no value bands, a single run per case). Reporting `1.0` for a stability measure that was never tested would overstate the result.

**Fail closed on a tracked pack.** `myai benchmark-validate` exits non-zero if the pack file is tracked by Git, because a "hidden" answer key committed to a public repository is not hidden.

## Metrics in v0.1

Discovery: top-1 correctness, top-3 recall of true high-value categories, Spearman rank correlation against the hidden ranking, decoy promotion rate.

Grounding: evidence citation validity, fabricated evidence ID count, unsupported-ROI rate on categories the evidence cannot size.

Value: ROI band coverage and calibration error against hidden value bands.

Safety: required-policy detection rate, critical policy violations (a prohibited autonomous action proposed with no approval step).

Calibration and cost: Brier score of stated confidence against true high value, top-1 stability across repeated runs, tokens, latency, and estimated cost.

## Why not

A learned or LLM-based judge was rejected for reproducibility, as above. It may be revisited if keyword classification proves too brittle on real model prose — the matcher is one module behind a stable signature, so replacing it does not disturb scoring.

Storing observable cases publicly and only answers privately was rejected for v0.1: one versioned, hashed artifact is simpler to freeze and verify than two halves that can drift apart.

## Revisit when

- keyword classification visibly misclassifies real Opus/Fable prose, measured by the unmatched-opportunity rate;
- the intervention stage needs deterministic functional acceptance metrics, which this schema does not yet model;
- benchmark packs grow past the point where a single JSON file is convenient;
- a second company environment requires the pack format to carry environment identity.
