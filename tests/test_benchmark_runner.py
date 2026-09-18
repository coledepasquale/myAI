from pathlib import Path

import pytest
from pydantic import BaseModel

from myai.baseline import BaselineOutput
from myai.benchmark import BenchmarkPack, FilesystemPackLoader
from myai.benchmark.runner import run_benchmark_suite
from myai.domain import Opportunity
from myai.model_gateway import ModelRequest, ModelResult

TOY_PACK = Path(__file__).parent / "data" / "toy_pack"


class FakeGateway:
    """Deterministic StructuredModel: answers toy-001 correctly, fails on demand."""

    provider_name = "fake"

    def __init__(self, fail_case_substring: str | None = None) -> None:
        self.fail_case_substring = fail_case_substring
        self.requests: list[ModelRequest] = []

    def generate[T: BaseModel](
        self, request: ModelRequest, schema: type[T]
    ) -> ModelResult[T]:
        self.requests.append(request)
        if self.fail_case_substring and self.fail_case_substring in request.user:
            raise RuntimeError("simulated provider outage")
        evidence_id = request.user.split('"id": "')[1].split('"')[0]
        output = BaselineOutput(
            opportunities=[
                Opportunity(
                    title="Automate the alpha workflow",
                    problem="Manual alpha effort.",
                    proposed_change="Draft alpha work for human approval.",
                    annual_value_usd=100_000,
                    confidence=0.9,
                    feasibility=0.8,
                    evidence_ids=[evidence_id],  # type: ignore[list-item]
                )
            ]
        )
        value = schema.model_validate(output.model_dump())
        return ModelResult[T](
            value=value,
            provider="fake",
            model=request.model,
            input_tokens=100,
            output_tokens=200,
            latency_ms=5,
            cost_usd=0.001,
        )


@pytest.fixture
def pack() -> BenchmarkPack:
    return FilesystemPackLoader(TOY_PACK).load()


def test_suite_scores_every_case_and_persists_artifacts(
    pack: BenchmarkPack, tmp_path: Path
) -> None:
    result = run_benchmark_suite(pack, FakeGateway(), "fake-model", repo_root=tmp_path)

    assert result.record.case_count == 2
    assert result.record.succeeded == 2
    assert result.report.run_count == 2
    assert result.report.pack_hash == pack.pack_hash
    # toy-001's true winner is alpha; toy-002's is beta — one hit, one miss.
    assert result.report.top1_accuracy == pytest.approx(0.5)

    assert result.run_dir is not None
    names = {item.name for item in result.run_dir.iterdir()}
    assert {"suite.json", "report.json"} <= names
    for case_id in ("toy-001", "toy-002"):
        expected = {f"{case_id}.request.json", f"{case_id}.output.json", f"{case_id}.score.json"}
        assert expected <= names


def test_prompts_never_contain_hidden_answers(pack: BenchmarkPack) -> None:
    gateway = FakeGateway()
    run_benchmark_suite(pack, gateway, "fake-model")

    for request in gateway.requests:
        payload = request.system + request.user
        assert "true_ranking" not in payload
        assert "delta_decoy" not in payload
        assert "Alpha is genuinely the largest win" not in payload


def test_failed_case_is_excluded_from_report_but_recorded(
    pack: BenchmarkPack, tmp_path: Path
) -> None:
    # toy-002's evidence mentions "consumes most of the team's day".
    gateway = FakeGateway(fail_case_substring="consumes most")
    result = run_benchmark_suite(pack, gateway, "fake-model", repo_root=tmp_path)

    assert result.record.succeeded == 1
    assert result.record.failed_case_ids == ["toy-002"]
    assert result.report.run_count == 1
    assert result.run_dir is not None
    assert (result.run_dir / "toy-002.error.txt").exists()
    assert not (result.run_dir / "toy-002.score.json").exists()


def test_limit_and_repeat_control_paid_call_volume(pack: BenchmarkPack) -> None:
    gateway = FakeGateway()
    result = run_benchmark_suite(pack, gateway, "fake-model", limit=1, repeat=3)

    assert len(gateway.requests) == 3
    assert result.record.case_count == 1
    assert result.report.run_count == 3
    # Deterministic fake output means perfect top-1 agreement across repeats.
    assert result.report.top1_stability == pytest.approx(1.0)


def test_prompt_version_flows_into_requests_and_record(pack: BenchmarkPack) -> None:
    gateway = FakeGateway()
    result = run_benchmark_suite(
        pack, gateway, "fake-model", prompt_version="baseline-v0.2"
    )

    assert result.record.prompt_version == "baseline-v0.2"
    assert all(req.prompt_version == "baseline-v0.2" for req in gateway.requests)
    assert all("Value discipline" in req.system for req in gateway.requests)
    assert all(run.prompt_version == "baseline-v0.2" for run in
               (o.run for o in result.outcomes) if run is not None)


def test_rescore_reproduces_stored_run_and_guards_pack_identity(
    pack: BenchmarkPack, tmp_path: Path
) -> None:
    from myai.benchmark.runner import rescore_run_dir

    live = run_benchmark_suite(pack, FakeGateway(), "fake-model", repo_root=tmp_path)
    assert live.run_dir is not None

    rescored = rescore_run_dir(live.run_dir, pack)

    assert rescored.top1_accuracy == live.report.top1_accuracy
    assert rescored.mean_top3_recall == live.report.mean_top3_recall
    assert rescored.mean_evidence_citation_validity == live.report.mean_evidence_citation_validity
    assert rescored.pack_hash == pack.pack_hash

    other = pack.model_copy(update={"pack_version": "different"})
    with pytest.raises(ValueError, match="refusing to rescore"):
        rescore_run_dir(live.run_dir, other)


def test_disk_write_failure_does_not_lose_paid_results(
    pack: BenchmarkPack, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import myai.benchmark.runner as runner_module

    monkeypatch.setattr(
        runner_module, "_persist", lambda path, text: f"{path.name}: disk full"
    )

    result = run_benchmark_suite(pack, FakeGateway(), "fake-model", repo_root=tmp_path)

    # Every paid result is still scored and reported despite zero artifacts landing.
    assert result.record.succeeded == 2
    assert result.report.run_count == 2
    assert result.report.top1_accuracy is not None
    assert len(result.record.artifact_write_errors) == 8  # 3 per case + suite + report
    assert "disk full" in result.record.artifact_write_errors[0]


def test_suite_without_repo_root_persists_nothing(pack: BenchmarkPack) -> None:
    result = run_benchmark_suite(pack, FakeGateway(), "fake-model")
    assert result.run_dir is None
