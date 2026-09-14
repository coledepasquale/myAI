from pathlib import Path

from myai.fixtures import northstar_fixture


def test_northstar_fixture_loads() -> None:
    fixture = northstar_fixture(Path.cwd())
    company = fixture.company()
    evidence = fixture.evidence()

    assert company["company_id"] == "northstar-industrial-services"
    assert company["employee_count"] == 82
    assert len(evidence) >= 8
    assert all(item.source for item in evidence)
