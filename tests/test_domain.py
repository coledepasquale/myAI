from uuid import UUID

import pytest

from myai.domain import Assumption, Evidence, EvidenceKind, Opportunity
from myai.evidence import EvidenceStore


def test_evidence_store_resolves_items() -> None:
    evidence = Evidence(kind=EvidenceKind.METRIC, source="test", content="42 events")
    store = EvidenceStore([evidence])
    assert store.get(evidence.id) == evidence
    assert store.resolve([evidence.id]) == [evidence]


def test_evidence_store_rejects_duplicate_ids() -> None:
    evidence = Evidence(kind=EvidenceKind.DOCUMENT, source="test", content="policy")
    store = EvidenceStore([evidence])
    with pytest.raises(ValueError):
        store.add(evidence)


def test_opportunity_priority_score_uses_value_confidence_feasibility_and_cost() -> None:
    opportunity = Opportunity(
        title="Automate routine quote preparation",
        problem="Routine quotes require repeated system lookups.",
        proposed_change="Prepare draft quotes automatically with human approval.",
        annual_value_usd=100_000,
        confidence=0.8,
        feasibility=0.5,
        implementation_cost_usd=10_000,
        evidence_ids=[UUID("11111111-1111-4111-8111-111111111111")],
        assumptions=[
            Assumption(statement="Volume remains stable", rationale="Trailing 12m", confidence=0.7)
        ],
    )
    assert opportunity.priority_score == pytest.approx(4.0)
