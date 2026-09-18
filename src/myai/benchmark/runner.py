"""Run a model over every case of a frozen benchmark pack and score the results.

The runner is the bridge between the observable half of a pack and the existing
Anthropic gateway. It reuses the frozen baseline-v0.1 prompt unchanged, persists
immutable per-case artifacts under ``runs/``, scores each output against the
hidden answers, and aggregates a report stamped with the pack hash.

A failed case is recorded loudly and excluded from the report; it can never
silently count as a valid benchmark observation.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from myai.baseline import BaselineOutput, build_context_request, request_input_hash
from myai.benchmark.categories import predicted_category_order
from myai.benchmark.report import BenchmarkReport, CaseRun, build_report
from myai.benchmark.schema import BenchmarkPack
from myai.benchmark.scoring import SCORER_VERSION, score_case
from myai.model_gateway import StructuredModel


class CaseOutcome(BaseModel):
    """What happened to one case in one suite run."""

    case_id: str
    ok: bool
    error: str | None = None
    run: CaseRun | None = None


class SuiteRecord(BaseModel):
    """Immutable metadata for one full benchmark suite run."""

    id: str
    model: str
    pack_version: str
    pack_hash: str
    scorer_version: str = SCORER_VERSION
    effort: str = "high"
    prompt_version: str = "baseline-v0.1"
    artifact_write_errors: list[str] = Field(default_factory=list)
    started_at: datetime
    repeat: int = Field(ge=1)
    case_count: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed_case_ids: list[str] = Field(default_factory=list)


class SuiteResult(BaseModel):
    record: SuiteRecord
    report: BenchmarkReport
    outcomes: list[CaseOutcome]
    run_dir: Path | None = None


ProgressFn = Callable[[CaseOutcome], None]


def _persist(path: Path, text: str) -> str | None:
    """Best-effort artifact write. A full disk must not lose a paid model result:
    the scored outcome stays in memory and the failure is reported on the record."""
    try:
        path.write_text(text)
    except OSError as exc:
        return f"{path.name}: {exc}"
    return None


def rescore_run_dir(run_dir: Path, pack: BenchmarkPack) -> BenchmarkReport:
    """Re-score a stored suite's outputs under the current scorer — no API calls.

    This is the scorer-upgrade path promised in ADR 0002: because every run
    persists its raw outputs, a matcher/scoring change can be applied uniformly
    to history. Operational metadata (tokens/latency/cost) is not recomputed.
    """
    record = SuiteRecord.model_validate_json((run_dir / "suite.json").read_text())
    if record.pack_hash != pack.pack_hash:
        raise ValueError(
            f"run {record.id} was measured against pack {record.pack_hash[:16]}…, "
            f"not the loaded pack {pack.pack_hash[:16]}… — refusing to rescore"
        )
    runs: list[CaseRun] = []
    for output_file in sorted(run_dir.glob("*.output.json")):
        case_id = output_file.name.split(".output.json")[0].split("#")[0]
        case = pack.case(case_id)
        output = BaselineOutput.model_validate_json(output_file.read_text())
        request_file = run_dir / output_file.name.replace(".output.", ".request.")
        input_hash = ""
        prompt_version = record.prompt_version
        if request_file.is_file():
            from myai.model_gateway import ModelRequest

            stored_request = ModelRequest.model_validate_json(request_file.read_text())
            input_hash = request_input_hash(stored_request)
            prompt_version = stored_request.prompt_version
        score = score_case(case, pack.answer(case_id), pack.category_rules, output)
        predicted = predicted_category_order(output.opportunities, pack.category_rules)
        runs.append(
            CaseRun(
                score=score,
                model=record.model,
                prompt_version=prompt_version,
                input_hash=input_hash,
                predicted_top1=predicted[0] if predicted else None,
            )
        )
    if not runs:
        raise ValueError(f"no output artifacts found in {run_dir}")
    return build_report(pack.pack_version, pack.pack_hash, record.model, runs)


def run_benchmark_suite(
    pack: BenchmarkPack,
    gateway: StructuredModel,
    model: str,
    *,
    repo_root: Path | None = None,
    limit: int | None = None,
    repeat: int = 1,
    effort: str = "high",
    prompt_version: str = "baseline-v0.1",
    on_case: ProgressFn | None = None,
) -> SuiteResult:
    """Execute ``repeat`` runs of each (limited) pack case and score them.

    ``repo_root=None`` skips artifact persistence (used by dry wiring tests).
    """
    started = datetime.now(UTC)
    suite_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    run_dir: Path | None = None
    if repo_root is not None:
        run_dir = repo_root / "runs" / f"benchmark_{suite_id}_{model}"
        run_dir.mkdir(parents=True, exist_ok=False)

    cases = pack.observable_cases()[: limit if limit is not None else len(pack.cases)]
    outcomes: list[CaseOutcome] = []
    write_errors: list[str] = []
    for case in cases:
        request = build_context_request(
            case.company, case.evidence, model, effort=effort, prompt_version=prompt_version
        )
        input_hash = request_input_hash(request)
        for attempt in range(1, repeat + 1):
            label = case.case_id if repeat == 1 else f"{case.case_id}#{attempt}"
            try:
                result = gateway.generate(request, BaselineOutput)
                score = score_case(
                    case, pack.answer(case.case_id), pack.category_rules, result.value
                )
                predicted = predicted_category_order(
                    result.value.opportunities, pack.category_rules
                )
                run = CaseRun(
                    score=score,
                    model=model,
                    prompt_version=request.prompt_version,
                    input_hash=input_hash,
                    predicted_top1=predicted[0] if predicted else None,
                    latency_ms=result.latency_ms,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=result.cost_usd,
                )
                outcome = CaseOutcome(case_id=case.case_id, ok=True, run=run)
                if run_dir is not None:
                    for name, payload in (
                        (f"{label}.request.json", request.model_dump_json(indent=2)),
                        (f"{label}.output.json", result.value.model_dump_json(indent=2)),
                        (f"{label}.score.json", run.model_dump_json(indent=2)),
                    ):
                        error = _persist(run_dir / name, payload + "\n")
                        if error is not None:
                            write_errors.append(error)
            except Exception as exc:  # noqa: BLE001 - a case failure must not kill the suite
                outcome = CaseOutcome(case_id=case.case_id, ok=False, error=str(exc))
                if run_dir is not None:
                    error = _persist(run_dir / f"{label}.error.txt", str(exc) + "\n")
                    if error is not None:
                        write_errors.append(error)
            outcomes.append(outcome)
            if on_case is not None:
                on_case(outcome)

    succeeded = [outcome.run for outcome in outcomes if outcome.run is not None]
    report = build_report(pack.pack_version, pack.pack_hash, model, succeeded)
    record = SuiteRecord(
        id=suite_id,
        model=model,
        pack_version=pack.pack_version,
        pack_hash=pack.pack_hash,
        started_at=started,
        repeat=repeat,
        effort=effort,
        prompt_version=prompt_version,
        artifact_write_errors=write_errors,
        case_count=len(cases),
        succeeded=len(succeeded),
        failed_case_ids=sorted({o.case_id for o in outcomes if not o.ok}),
    )
    if run_dir is not None:
        for name, payload in (
            ("suite.json", record.model_dump_json(indent=2)),
            ("report.json", report.model_dump_json(indent=2)),
        ):
            error = _persist(run_dir / name, payload + "\n")
            if error is not None:
                record.artifact_write_errors.append(error)
    return SuiteResult(record=record, report=report, outcomes=outcomes, run_dir=run_dir)
