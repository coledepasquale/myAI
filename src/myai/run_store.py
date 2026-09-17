from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from myai.baseline import BaselineOutput
from myai.model_gateway import ModelRequest, ModelResult


class BaselineRunMetadata(BaseModel):
    id: UUID
    experiment: str = "baseline-v0.1"
    environment: str
    provider: str
    model: str
    prompt_version: str
    input_hash: str
    created_at: datetime
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    opportunity_count: int = Field(ge=0)
    evidence_citation_count: int = Field(ge=0)
    invalid_evidence_ids: list[UUID] = Field(default_factory=list)


def save_baseline_run(
    repo_root: Path,
    environment: str,
    request: ModelRequest,
    result: ModelResult[BaselineOutput],
    input_hash: str,
    known_evidence_ids: set[UUID],
) -> tuple[Path, BaselineRunMetadata]:
    run_id = uuid4()
    now = datetime.now(UTC)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_dir = repo_root / "runs" / f"{stamp}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)

    cited_ids = [
        evidence_id
        for opportunity in result.value.opportunities
        for evidence_id in opportunity.evidence_ids
    ]
    invalid_ids = sorted(
        {evidence_id for evidence_id in cited_ids if evidence_id not in known_evidence_ids},
        key=str,
    )

    metadata = BaselineRunMetadata(
        id=run_id,
        environment=environment,
        provider=result.provider,
        model=result.model,
        prompt_version=request.prompt_version,
        input_hash=input_hash,
        created_at=now,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        opportunity_count=len(result.value.opportunities),
        evidence_citation_count=len(cited_ids),
        invalid_evidence_ids=invalid_ids,
    )

    (run_dir / "request.json").write_text(request.model_dump_json(indent=2) + "\n")
    (run_dir / "output.json").write_text(result.value.model_dump_json(indent=2) + "\n")
    (run_dir / "run.json").write_text(metadata.model_dump_json(indent=2) + "\n")
    if result.raw_text is not None:
        (run_dir / "raw_response.txt").write_text(result.raw_text)

    return run_dir, metadata
