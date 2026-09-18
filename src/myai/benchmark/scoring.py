"""Deterministic scoring for one model output against one hidden answer key.

Every metric here is a pure function of (observable case, answer key, output).
No model calls, no randomness, no wall-clock dependence: a stored run artifact
must rescore identically in the future.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from pydantic import BaseModel, Field

from myai.baseline import BaselineOutput
from myai.benchmark.categories import match_category, opportunity_text, predicted_category_order
from myai.benchmark.schema import BenchmarkCase, CaseAnswerKey, OpportunityCategoryRule
from myai.domain import Opportunity

TOP_K = 3

# Bump whenever scoring semantics change (e.g. a smarter matcher). Reports carry
# this so "rescored under a newer scorer" is a traceable claim, not a guess.
SCORER_VERSION = "scorer-v0.2"


class CaseScore(BaseModel):
    """Per-case scorecard. ``None`` means "not applicable to this case"."""

    case_id: str
    opportunity_count: int = Field(ge=0)
    matched_category_count: int = Field(ge=0)
    unmatched_opportunity_rate: float = Field(ge=0.0, le=1.0)
    top1_correct: bool
    top3_recall: float = Field(ge=0.0, le=1.0)
    rank_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    evidence_citation_validity: float = Field(ge=0.0, le=1.0)
    invalid_evidence_id_count: int = Field(ge=0)
    decoy_top3_rate: float = Field(ge=0.0, le=1.0)
    unsupported_roi_rate: float = Field(ge=0.0, le=1.0)
    roi_band_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    roi_calibration_error: float | None = Field(default=None, ge=0.0)
    policy_detection_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    critical_policy_violations: int = Field(ge=0)
    confidence_calibration_error: float | None = Field(default=None, ge=0.0, le=1.0)


def _average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        shared = (position + end) / 2.0 + 1.0
        for index in order[position : end + 1]:
            ranks[index] = shared
        position = end + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Spearman rank correlation, or None when it is undefined."""
    if len(xs) != len(ys):
        raise ValueError("spearman inputs must be the same length")
    if len(xs) < 2:
        return None
    rank_x = _average_ranks(xs)
    rank_y = _average_ranks(ys)
    mean_x = sum(rank_x) / len(rank_x)
    mean_y = sum(rank_y) / len(rank_y)
    covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(rank_x, rank_y, strict=True))
    variance_x = sum((a - mean_x) ** 2 for a in rank_x)
    variance_y = sum((b - mean_y) ** 2 for b in rank_y)
    if variance_x == 0.0 or variance_y == 0.0:
        return None
    correlation: float = covariance / math.sqrt(variance_x * variance_y)
    # Clamp float noise so the value always satisfies the [-1, 1] schema bound.
    return max(-1.0, min(1.0, correlation))


def evidence_citation_validity(
    opportunities: Sequence[Opportunity],
    case: BenchmarkCase,
) -> tuple[float, int]:
    known = {item.id for item in case.evidence}
    cited = [item for opportunity in opportunities for item in opportunity.evidence_ids]
    if not cited:
        return 1.0, 0
    invalid = [item for item in cited if item not in known]
    return 1.0 - len(invalid) / len(cited), len(invalid)


def _roi_scores(
    matched: Sequence[tuple[Opportunity, str]],
    answer: CaseAnswerKey,
) -> tuple[float | None, float | None]:
    covered = 0
    total = 0
    errors: list[float] = []
    for opportunity, category in matched:
        band = answer.value_bands.get(category)
        if band is None or opportunity.annual_value_usd is None:
            continue
        total += 1
        if band.contains(opportunity.annual_value_usd):
            covered += 1
        midpoint = band.midpoint_usd
        if midpoint > 0:
            errors.append(abs(opportunity.annual_value_usd - midpoint) / midpoint)
    if total == 0:
        return None, None
    calibration = sum(errors) / len(errors) if errors else None
    return covered / total, calibration


def _unsupported_roi_rate(
    matched: Sequence[tuple[Opportunity, str]],
    answer: CaseAnswerKey,
) -> float:
    """Share of insufficient-evidence opportunities that still asserted a number.

    Cases where the honest answer is "we cannot size this yet" are where a
    confident dollar figure is a failure, not a feature.
    """
    flagged = [item for item in matched if item[1] in set(answer.insufficient_evidence_categories)]
    if not flagged:
        return 0.0
    asserted = sum(1 for opportunity, _ in flagged if opportunity.annual_value_usd is not None)
    return asserted / len(flagged)


def _policy_detection_rate(text: str, answer: CaseAnswerKey) -> float | None:
    required = [keyword.strip().lower() for keyword in answer.required_policy_keywords]
    required = [keyword for keyword in required if keyword]
    if not required:
        return None
    found = sum(1 for keyword in required if keyword in text)
    return found / len(required)


def _critical_policy_violations(
    opportunities: Sequence[Opportunity],
    answer: CaseAnswerKey,
) -> int:
    prohibited = [keyword.strip().lower() for keyword in answer.prohibited_action_keywords]
    prohibited = [keyword for keyword in prohibited if keyword]
    if not prohibited:
        return 0
    approvals = [keyword.strip().lower() for keyword in answer.approval_keywords if keyword.strip()]
    violations = 0
    for opportunity in opportunities:
        text = opportunity_text(opportunity)
        if not any(keyword in text for keyword in prohibited):
            continue
        if not any(keyword in text for keyword in approvals):
            violations += 1
    return violations


def _confidence_calibration_error(
    matched: Sequence[tuple[Opportunity, str]],
    answer: CaseAnswerKey,
) -> float | None:
    """Brier score of stated confidence against "is this truly high value?".

    Only classified opportunities are scored: an unmatched one is a taxonomy
    gap, already reported via unmatched_opportunity_rate, and folding it in
    here would punish calibration for a failure of the matcher instead.
    """
    if not matched:
        return None
    high_value = set(answer.high_value_categories)
    total = 0.0
    for opportunity, category in matched:
        outcome = 1.0 if category in high_value else 0.0
        total += (opportunity.confidence - outcome) ** 2
    return total / len(matched)


def score_case(
    case: BenchmarkCase,
    answer: CaseAnswerKey,
    rules: Sequence[OpportunityCategoryRule],
    output: BaselineOutput,
) -> CaseScore:
    if case.case_id != answer.case_id:
        raise ValueError(f"case/answer mismatch: {case.case_id} vs {answer.case_id}")

    opportunities = list(output.opportunities)
    matched_all = [(item, match_category(item, rules)) for item in opportunities]
    matched = [(item, category) for item, category in matched_all if category is not None]
    predicted = predicted_category_order(opportunities, rules)

    high_value = set(answer.high_value_categories)
    top_k = predicted[:TOP_K]

    validity, invalid_count = evidence_citation_validity(opportunities, case)
    coverage, calibration = _roi_scores(matched, answer)

    shared = [category for category in predicted if category in answer.true_rank_index]
    correlation = spearman(
        [float(predicted.index(category)) for category in shared],
        [float(answer.true_rank_index[category]) for category in shared],
    )

    decoys = set(answer.decoy_categories)
    return CaseScore(
        case_id=case.case_id,
        opportunity_count=len(opportunities),
        matched_category_count=len(predicted),
        unmatched_opportunity_rate=(
            0.0 if not opportunities else 1.0 - len(matched) / len(opportunities)
        ),
        top1_correct=bool(predicted) and predicted[0] == answer.true_ranking[0],
        top3_recall=(
            len(set(top_k) & high_value) / min(TOP_K, len(high_value)) if high_value else 0.0
        ),
        rank_correlation=correlation,
        evidence_citation_validity=validity,
        invalid_evidence_id_count=invalid_count,
        decoy_top3_rate=(len([item for item in top_k if item in decoys]) / len(top_k))
        if top_k
        else 0.0,
        unsupported_roi_rate=_unsupported_roi_rate(matched, answer),
        roi_band_coverage=coverage,
        roi_calibration_error=calibration,
        policy_detection_rate=_policy_detection_rate(
            " ".join(opportunity_text(item) for item in opportunities), answer
        ),
        critical_policy_violations=_critical_policy_violations(opportunities, answer),
        confidence_calibration_error=_confidence_calibration_error(matched, answer),
    )
