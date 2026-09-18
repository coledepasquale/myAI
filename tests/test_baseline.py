from pathlib import Path
from uuid import UUID

import pytest

from myai.baseline import BaselineOutput, baseline_input_hash, build_baseline_request
from myai.domain import Opportunity
from myai.fixtures import northstar_fixture
from myai.model_gateway import ModelResult
from myai.providers.anthropic import estimate_cost_usd
from myai.run_store import save_baseline_run


def test_baseline_input_hash_is_stable() -> None:
    fixture = northstar_fixture(Path.cwd())
    first = baseline_input_hash(fixture, "claude-sonnet-5")
    second = baseline_input_hash(fixture, "claude-sonnet-5")
    assert first == second
    assert len(first) == 64


def test_anthropic_cost_estimate_uses_versioned_rates() -> None:
    assert estimate_cost_usd("claude-sonnet-5", 1_000_000, 1_000_000) == pytest.approx(12.0)
    assert estimate_cost_usd("claude-opus-5", 1_000_000, 1_000_000) == pytest.approx(30.0)
    assert estimate_cost_usd("claude-fable-5-1", 1_000_000, 1_000_000) == pytest.approx(60.0)
    assert estimate_cost_usd("unknown-model", 1_000, 1_000) is None


def test_v01_prompt_is_frozen_by_hash() -> None:
    # The v0.1 control is frozen: this hash matches the recorded 2026-09-17 smoke
    # run and the official 2026-09-18 baseline suites. If this test fails, the
    # prompt or fixture changed and comparisons with recorded runs are void.
    fixture = northstar_fixture(Path.cwd())
    assert (
        baseline_input_hash(fixture, "claude-sonnet-5")
        == "89f65eef7ed153c4e67ae4aab0abba6c2333ada499d0cfdba584a93f62d67a28"
    )


def test_v02_is_a_distinct_tracked_prompt_version() -> None:
    from myai.baseline import build_context_request

    fixture = northstar_fixture(Path.cwd())
    v01 = build_context_request(fixture.company(), fixture.evidence(), "claude-opus-5")
    v02 = build_context_request(
        fixture.company(), fixture.evidence(), "claude-opus-5",
        prompt_version="baseline-v0.2",
    )

    assert v02.prompt_version == "baseline-v0.2"
    assert v02.system.startswith(v01.system)  # v0.2 only appends; the core is shared
    assert "annual_value_usd" in v02.system and "null" in v02.system
    assert v02.user == v01.user  # observable context identical across versions

    with pytest.raises(ValueError, match="unknown prompt version"):
        build_context_request(
            fixture.company(), fixture.evidence(), "claude-opus-5",
            prompt_version="baseline-v9",
        )


def test_requests_record_explicit_effort() -> None:
    fixture = northstar_fixture(Path.cwd())
    default = build_baseline_request(fixture, "claude-sonnet-5")
    assert default.effort == "high"  # matches the documented API default, now explicit

    from myai.baseline import build_context_request

    tuned = build_context_request(fixture.company(), fixture.evidence(), "claude-opus-5", "xhigh")
    assert tuned.effort == "xhigh"
    assert tuned.prompt_version == default.prompt_version


def test_run_store_persists_request_output_and_citation_quality(tmp_path: Path) -> None:
    fixture = northstar_fixture(Path.cwd())
    request = build_baseline_request(fixture, "claude-sonnet-5")
    known_id = fixture.evidence()[0].id
    invalid_id = UUID("99999999-9999-4999-8999-999999999999")
    output = BaselineOutput(
        opportunities=[
            Opportunity(
                title="Assisted quote preparation",
                problem="Quote preparation requires repeated lookups.",
                proposed_change="Draft routine quotes for human approval.",
                annual_value_usd=100_000,
                confidence=0.8,
                feasibility=0.9,
                implementation_cost_usd=15_000,
                evidence_ids=[known_id, invalid_id],
            )
        ]
    )
    result = ModelResult[BaselineOutput](
        value=output,
        provider="anthropic",
        model="claude-sonnet-5",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=250,
        cost_usd=0.007,
    )

    run_dir, metadata = save_baseline_run(
        repo_root=tmp_path,
        environment="northstar",
        request=request,
        result=result,
        input_hash=baseline_input_hash(fixture, "claude-sonnet-5"),
        known_evidence_ids={item.id for item in fixture.evidence()},
    )

    assert (run_dir / "request.json").exists()
    assert (run_dir / "output.json").exists()
    assert (run_dir / "run.json").exists()
    assert metadata.opportunity_count == 1
    assert metadata.evidence_citation_count == 2
    assert metadata.invalid_evidence_ids == [invalid_id]
