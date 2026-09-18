"""Aggregation of per-case scores into a comparable benchmark report.

A report is always stamped with the pack version and pack hash. A number that
cannot be traced to a frozen target is not a benchmark result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from statistics import mean

from pydantic import BaseModel, Field

from myai.benchmark.scoring import SCORER_VERSION, CaseScore


class CaseRun(BaseModel):
    """One model output scored against one case, plus operational metadata."""

    score: CaseScore
    model: str
    prompt_version: str
    input_hash: str
    predicted_top1: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)


class BenchmarkReport(BaseModel):
    pack_version: str
    pack_hash: str
    scorer_version: str = SCORER_VERSION
    model: str
    run_count: int = Field(ge=0)
    case_count: int = Field(ge=0)
    top1_accuracy: float | None = None
    mean_top3_recall: float | None = None
    mean_unmatched_opportunity_rate: float | None = None
    mean_rank_correlation: float | None = None
    mean_evidence_citation_validity: float | None = None
    total_invalid_evidence_ids: int = Field(default=0, ge=0)
    mean_decoy_top3_rate: float | None = None
    mean_unsupported_roi_rate: float | None = None
    mean_roi_band_coverage: float | None = None
    mean_roi_calibration_error: float | None = None
    mean_policy_detection_rate: float | None = None
    total_critical_policy_violations: int = Field(default=0, ge=0)
    mean_confidence_calibration_error: float | None = None
    top1_stability: float | None = None
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)
    total_cost_usd: float | None = None
    mean_latency_ms: float | None = None


def _mean_of(values: Sequence[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def top1_stability(runs: Sequence[CaseRun]) -> float | None:
    """Share of repeated runs that agree with their case's most common top-1.

    Cases run only once carry no stability information and are excluded, so a
    single-run suite reports ``None`` rather than a misleading 1.0.
    """
    by_case: dict[str, list[str | None]] = defaultdict(list)
    for run in runs:
        by_case[run.score.case_id].append(run.predicted_top1)
    repeated = [picks for picks in by_case.values() if len(picks) > 1]
    if not repeated:
        return None
    agreements = []
    for picks in repeated:
        modal_count = Counter(picks).most_common(1)[0][1]
        agreements.append(modal_count / len(picks))
    return mean(agreements)


def build_report(
    pack_version: str,
    pack_hash: str,
    model: str,
    runs: Sequence[CaseRun],
) -> BenchmarkReport:
    if any(run.model != model for run in runs):
        raise ValueError("a report must aggregate runs from a single model")

    scores = [run.score for run in runs]
    latencies = [float(run.latency_ms) if run.latency_ms is not None else None for run in runs]
    costs = [run.cost_usd for run in runs if run.cost_usd is not None]
    return BenchmarkReport(
        pack_version=pack_version,
        pack_hash=pack_hash,
        model=model,
        run_count=len(runs),
        case_count=len({score.case_id for score in scores}),
        top1_accuracy=(
            mean(1.0 if score.top1_correct else 0.0 for score in scores) if scores else None
        ),
        mean_top3_recall=_mean_of([score.top3_recall for score in scores]),
        mean_unmatched_opportunity_rate=_mean_of(
            [score.unmatched_opportunity_rate for score in scores]
        ),
        mean_rank_correlation=_mean_of([score.rank_correlation for score in scores]),
        mean_evidence_citation_validity=_mean_of(
            [score.evidence_citation_validity for score in scores]
        ),
        total_invalid_evidence_ids=sum(score.invalid_evidence_id_count for score in scores),
        mean_decoy_top3_rate=_mean_of([score.decoy_top3_rate for score in scores]),
        mean_unsupported_roi_rate=_mean_of([score.unsupported_roi_rate for score in scores]),
        mean_roi_band_coverage=_mean_of([score.roi_band_coverage for score in scores]),
        mean_roi_calibration_error=_mean_of([score.roi_calibration_error for score in scores]),
        mean_policy_detection_rate=_mean_of([score.policy_detection_rate for score in scores]),
        total_critical_policy_violations=sum(score.critical_policy_violations for score in scores),
        mean_confidence_calibration_error=_mean_of(
            [score.confidence_calibration_error for score in scores]
        ),
        top1_stability=top1_stability(runs),
        total_input_tokens=sum(run.input_tokens or 0 for run in runs),
        total_output_tokens=sum(run.output_tokens or 0 for run in runs),
        total_cost_usd=sum(costs) if costs else None,
        mean_latency_ms=_mean_of(latencies),
    )
