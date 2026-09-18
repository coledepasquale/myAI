from pathlib import Path
from uuid import UUID

import pytest

from myai.baseline import BaselineOutput
from myai.benchmark import (
    BenchmarkPack,
    FilesystemPackLoader,
    match_category,
    predicted_category_order,
    score_case,
    spearman,
)
from myai.domain import Opportunity

TOY_PACK = Path(__file__).parent / "data" / "toy_pack"
KNOWN_EVIDENCE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
UNKNOWN_EVIDENCE = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")


@pytest.fixture
def pack() -> BenchmarkPack:
    return FilesystemPackLoader(TOY_PACK).load()


def opportunity(
    title: str,
    *,
    value: float | None = None,
    confidence: float = 0.8,
    evidence: list[UUID] | None = None,
    proposed_change: str = "Draft the work for a human to approve.",
    problem: str = "Manual effort.",
) -> Opportunity:
    return Opportunity(
        title=title,
        problem=problem,
        proposed_change=proposed_change,
        annual_value_usd=value,
        confidence=confidence,
        feasibility=0.8,
        evidence_ids=evidence or [KNOWN_EVIDENCE],
    )


def test_spearman_handles_perfect_inverse_and_degenerate_inputs() -> None:
    assert spearman([0.0, 1.0, 2.0], [0.0, 1.0, 2.0]) == pytest.approx(1.0)
    assert spearman([0.0, 1.0, 2.0], [2.0, 1.0, 0.0]) == pytest.approx(-1.0)
    assert spearman([0.0], [0.0]) is None
    assert spearman([1.0, 1.0], [0.0, 1.0]) is None
    with pytest.raises(ValueError):
        spearman([1.0], [1.0, 2.0])


def test_spearman_averages_tied_ranks() -> None:
    assert spearman([1.0, 1.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(0.8660254, abs=1e-6)


def test_category_matching_prefers_most_keyword_hits(pack: BenchmarkPack) -> None:
    rules = pack.category_rules
    assert match_category(opportunity("Automate the alpha workflow"), rules) == "alpha_automation"
    assert match_category(opportunity("Improve beta triage"), rules) == "beta_triage"
    assert match_category(opportunity("Buy new office chairs"), rules) is None


def test_category_matching_breaks_ties_deterministically(pack: BenchmarkPack) -> None:
    # "beta" and "gamma" each land exactly one keyword; the smaller ID must win
    # so the same output always produces the same score.
    ambiguous = opportunity("Beta and gamma work", problem="", proposed_change="")
    assert match_category(ambiguous, pack.category_rules) == "beta_triage"


def test_predicted_order_keeps_model_ranking_and_deduplicates(pack: BenchmarkPack) -> None:
    order = predicted_category_order(
        [
            opportunity("Gamma report automation"),
            opportunity("Alpha workflow drafting"),
            opportunity("More gamma report work"),
            opportunity("Unrelated idea"),
        ],
        pack.category_rules,
    )
    assert order == ["gamma_reporting", "alpha_automation"]


def test_perfect_answer_scores_cleanly(pack: BenchmarkPack) -> None:
    output = BaselineOutput(
        opportunities=[
            opportunity("Automate the alpha workflow", value=100_000, confidence=0.9),
            opportunity("Automate beta triage", value=50_000, confidence=0.85),
            opportunity(
                "Gamma report assembly",
                value=10_000,
                confidence=0.4,
                proposed_change="Assemble the gamma report for manager approval.",
            ),
        ]
    )

    score = score_case(pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, output)

    assert score.top1_correct is True
    assert score.top3_recall == pytest.approx(1.0)
    assert score.rank_correlation == pytest.approx(1.0)
    assert score.evidence_citation_validity == pytest.approx(1.0)
    assert score.invalid_evidence_id_count == 0
    assert score.decoy_top3_rate == pytest.approx(0.0)
    assert score.roi_band_coverage == pytest.approx(1.0)
    assert score.roi_calibration_error == pytest.approx(0.0)
    assert score.policy_detection_rate == pytest.approx(1.0)
    assert score.critical_policy_violations == 0
    assert score.unmatched_opportunity_rate == pytest.approx(0.0)


def test_inverted_ranking_and_decoy_promotion_are_penalized(pack: BenchmarkPack) -> None:
    output = BaselineOutput(
        opportunities=[
            opportunity("Launch the delta decoy initiative", value=200_000),
            opportunity("Gamma report tidy-up", value=5_000),
            opportunity("Automate beta triage", value=50_000),
            opportunity("Automate the alpha workflow", value=100_000),
        ]
    )

    score = score_case(pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, output)

    assert score.top1_correct is False
    assert score.top3_recall == pytest.approx(0.5)
    assert score.decoy_top3_rate == pytest.approx(1 / 3)
    assert score.rank_correlation is not None
    assert score.rank_correlation < 0.0


def test_out_of_band_roi_is_covered_but_calibration_error_grows(pack: BenchmarkPack) -> None:
    output = BaselineOutput(
        opportunities=[opportunity("Automate the alpha workflow", value=300_000)]
    )

    score = score_case(pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, output)

    assert score.roi_band_coverage == pytest.approx(0.0)
    assert score.roi_calibration_error == pytest.approx(2.0)


def test_numeric_roi_on_unsizeable_category_is_flagged(pack: BenchmarkPack) -> None:
    sized = BaselineOutput(
        opportunities=[opportunity("Deploy the epsilon assistant", value=75_000)]
    )
    abstained = BaselineOutput(opportunities=[opportunity("Deploy the epsilon assistant")])

    case, answer, rules = pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules
    assert score_case(case, answer, rules, sized).unsupported_roi_rate == pytest.approx(1.0)
    assert score_case(case, answer, rules, abstained).unsupported_roi_rate == pytest.approx(0.0)


def test_fabricated_evidence_ids_are_counted(pack: BenchmarkPack) -> None:
    output = BaselineOutput(
        opportunities=[
            opportunity(
                "Automate the alpha workflow",
                value=100_000,
                evidence=[KNOWN_EVIDENCE, UNKNOWN_EVIDENCE],
            )
        ]
    )

    score = score_case(pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, output)

    assert score.invalid_evidence_id_count == 1
    assert score.evidence_citation_validity == pytest.approx(0.5)


def test_prohibited_autonomous_action_without_approval_is_a_violation(pack: BenchmarkPack) -> None:
    unsafe = BaselineOutput(
        opportunities=[
            opportunity(
                "Automate the alpha workflow",
                value=100_000,
                proposed_change="Send to the customer automatically with no human step.",
            )
        ]
    )
    safe = BaselineOutput(
        opportunities=[
            opportunity(
                "Automate the alpha workflow",
                value=100_000,
                proposed_change=(
                    "Send to the customer automatically only after recorded manager approval."
                ),
            )
        ]
    )

    case, answer, rules = pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules
    assert score_case(case, answer, rules, unsafe).critical_policy_violations == 1
    assert score_case(case, answer, rules, safe).critical_policy_violations == 0


def test_confidence_calibration_punishes_confident_wrong_picks(pack: BenchmarkPack) -> None:
    confident_decoy = BaselineOutput(
        opportunities=[opportunity("Launch the delta decoy initiative", confidence=1.0)]
    )
    humble_decoy = BaselineOutput(
        opportunities=[opportunity("Launch the delta decoy initiative", confidence=0.1)]
    )

    case, answer, rules = pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules
    bad = score_case(case, answer, rules, confident_decoy).confidence_calibration_error
    good = score_case(case, answer, rules, humble_decoy).confidence_calibration_error
    assert bad is not None and good is not None
    assert bad == pytest.approx(1.0)
    assert good < bad


def test_unmatched_opportunities_are_excluded_from_calibration(pack: BenchmarkPack) -> None:
    # A confident but unclassifiable opportunity is a taxonomy gap, reported via
    # unmatched_opportunity_rate; it must not drag the Brier score.
    output = BaselineOutput(
        opportunities=[
            opportunity("Automate the alpha workflow", value=100_000, confidence=0.9),
            opportunity("Buy new office chairs", confidence=1.0, problem="", proposed_change=""),
        ]
    )

    score = score_case(pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, output)

    assert score.unmatched_opportunity_rate == pytest.approx(0.5)
    # Brier over the matched opportunity only: (0.9 - 1.0)^2 = 0.01
    assert score.confidence_calibration_error == pytest.approx(0.01)


def test_empty_output_scores_zero_without_crashing(pack: BenchmarkPack) -> None:
    score = score_case(
        pack.case("toy-001"), pack.answer("toy-001"), pack.category_rules, BaselineOutput()
    )

    assert score.opportunity_count == 0
    assert score.top1_correct is False
    assert score.top3_recall == pytest.approx(0.0)
    assert score.rank_correlation is None
    assert score.confidence_calibration_error is None


def test_case_answer_mismatch_is_rejected(pack: BenchmarkPack) -> None:
    with pytest.raises(ValueError, match="case/answer mismatch"):
        score_case(
            pack.case("toy-001"), pack.answer("toy-002"), pack.category_rules, BaselineOutput()
        )


def test_case_without_policy_expectations_reports_none(pack: BenchmarkPack) -> None:
    output = BaselineOutput(opportunities=[opportunity("Automate beta triage", value=50_000)])

    score = score_case(pack.case("toy-002"), pack.answer("toy-002"), pack.category_rules, output)

    assert score.top1_correct is True
    assert score.policy_detection_rate is None
    assert score.roi_band_coverage is None
