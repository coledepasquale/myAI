import pytest

from myai.benchmark import BenchmarkReport, CaseRun, CaseScore, build_report, top1_stability


def case_score(case_id: str, *, top1: bool = True, recall: float = 1.0) -> CaseScore:
    return CaseScore(
        case_id=case_id,
        opportunity_count=3,
        matched_category_count=3,
        unmatched_opportunity_rate=0.0,
        top1_correct=top1,
        top3_recall=recall,
        rank_correlation=1.0 if top1 else -1.0,
        evidence_citation_validity=1.0,
        invalid_evidence_id_count=0 if top1 else 2,
        decoy_top3_rate=0.0,
        unsupported_roi_rate=0.0,
        critical_policy_violations=0 if top1 else 1,
        confidence_calibration_error=0.1,
    )


def case_run(
    case_id: str,
    *,
    top1: bool = True,
    predicted: str = "alpha",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cost_usd: float | None = None,
    latency_ms: int | None = None,
) -> CaseRun:
    return CaseRun(
        score=case_score(case_id, top1=top1),
        model="claude-opus-5",
        prompt_version="baseline-v0.1",
        input_hash="hash",
        predicted_top1=predicted,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


def test_report_aggregates_means_totals_and_metadata() -> None:
    runs = [
        case_run("c1", input_tokens=100, output_tokens=200, cost_usd=0.01, latency_ms=1000),
        case_run(
            "c2",
            top1=False,
            predicted="beta",
            input_tokens=150,
            output_tokens=250,
            cost_usd=0.02,
            latency_ms=3000,
        ),
    ]

    report = build_report("pack-v1", "abc123", "claude-opus-5", runs)

    assert report.run_count == 2
    assert report.case_count == 2
    assert report.top1_accuracy == pytest.approx(0.5)
    assert report.mean_unmatched_opportunity_rate == pytest.approx(0.0)
    assert report.mean_rank_correlation == pytest.approx(0.0)
    assert report.total_invalid_evidence_ids == 2
    assert report.total_critical_policy_violations == 1
    assert report.total_input_tokens == 250
    assert report.total_output_tokens == 450
    assert report.total_cost_usd == pytest.approx(0.03)
    assert report.mean_latency_ms == pytest.approx(2000.0)
    assert report.pack_hash == "abc123"
    assert report.scorer_version.startswith("scorer-v")


def test_report_refuses_to_mix_models() -> None:
    mixed = [case_run("c1"), case_run("c2").model_copy(update={"model": "claude-fable-5-1"})]

    with pytest.raises(ValueError, match="single model"):
        build_report("pack-v1", "abc123", "claude-opus-5", mixed)


def test_single_run_per_case_reports_no_stability_signal() -> None:
    assert top1_stability([case_run("c1"), case_run("c2")]) is None


def test_stability_measures_agreement_across_repeated_cases() -> None:
    stable = [case_run("c1", predicted="alpha"), case_run("c1", predicted="alpha")]
    split = [case_run("c2", predicted="alpha"), case_run("c2", predicted="beta")]

    assert top1_stability(stable) == pytest.approx(1.0)
    assert top1_stability(split) == pytest.approx(0.5)
    assert top1_stability(stable + split) == pytest.approx(0.75)


def test_empty_report_is_well_formed() -> None:
    report = build_report("pack-v1", "abc123", "claude-opus-5", [])

    assert isinstance(report, BenchmarkReport)
    assert report.run_count == 0
    assert report.top1_accuracy is None
    assert report.total_cost_usd is None
