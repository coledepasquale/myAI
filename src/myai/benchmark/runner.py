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


def run_benchmark_suite(
    pack: BenchmarkPack,
    gateway: StructuredModel,
    model: str,
    *,
    repo_root: Path | None = None,
    limit: int | None = None,
    repeat: int = 1,
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
    for case in cases:
        request = build_context_request(case.company, case.evidence, model)
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
                    (run_dir / f"{label}.request.json").write_text(
                        request.model_dump_json(indent=2) + "\n"
                    )
                    (run_dir / f"{label}.output.json").write_text(
                        result.value.model_dump_json(indent=2) + "\n"
                    )
                    (run_dir / f"{label}.score.json").write_text(
                        run.model_dump_json(indent=2) + "\n"
                    )
            except Exception as exc:  # noqa: BLE001 - a case failure must not kill the suite
                outcome = CaseOutcome(case_id=case.case_id, ok=False, error=str(exc))
                if run_dir is not None:
                    (run_dir / f"{label}.error.txt").write_text(str(exc) + "\n")
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
        case_count=len(cases),
        succeeded=len(succeeded),
        failed_case_ids=sorted({o.case_id for o in outcomes if not o.ok}),
    )
    if run_dir is not None:
        (run_dir / "suite.json").write_text(record.model_dump_json(indent=2) + "\n")
        (run_dir / "report.json").write_text(report.model_dump_json(indent=2) + "\n")
    return SuiteResult(record=record, report=report, outcomes=outcomes, run_dir=run_dir)
