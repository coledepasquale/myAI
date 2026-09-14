from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class EvidenceKind(StrEnum):
    DOCUMENT = "document"
    INTERVIEW = "interview"
    SYSTEM_RECORD = "system_record"
    OBSERVATION = "observation"
    METRIC = "metric"
    INFERENCE = "inference"


class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    kind: EvidenceKind
    source: str
    content: str
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Assumption(BaseModel):
    statement: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class WorkflowStep(BaseModel):
    id: str
    name: str
    actor: str
    system: str | None = None
    avg_minutes: float | None = Field(default=None, ge=0)
    frequency_per_year: float | None = Field(default=None, ge=0)
    evidence_ids: list[UUID] = Field(default_factory=list)


class Workflow(BaseModel):
    id: str
    name: str
    objective: str
    steps: list[WorkflowStep]
    evidence_ids: list[UUID] = Field(default_factory=list)


class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    problem: str
    proposed_change: str
    annual_value_usd: float | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    feasibility: float = Field(ge=0.0, le=1.0)
    implementation_cost_usd: float | None = Field(default=None, ge=0)
    evidence_ids: list[UUID] = Field(min_length=1)
    assumptions: list[Assumption] = Field(default_factory=list)

    @property
    def priority_score(self) -> float | None:
        if self.annual_value_usd is None:
            return None
        denominator = max(self.implementation_cost_usd or 1.0, 1.0)
        return self.annual_value_usd * self.confidence * self.feasibility / denominator


class Intervention(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    opportunity_id: UUID
    name: str
    description: str
    artifact_refs: list[str] = Field(default_factory=list)
    approval_required: bool = True


class EvaluationMetric(BaseModel):
    name: str
    before: float | None = None
    after: float | None = None
    unit: str
    higher_is_better: bool

    @property
    def delta(self) -> float | None:
        if self.before is None or self.after is None:
            return None
        return self.after - self.before


class Evaluation(BaseModel):
    intervention_id: UUID
    passed: bool
    metrics: list[EvaluationMetric]
    hidden_case_pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    policy_violations: int = Field(default=0, ge=0)
    notes: list[str] = Field(default_factory=list)


class ModelInvocation(BaseModel):
    provider: str
    model: str
    prompt_version: str
    input_hash: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)


class Run(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    experiment: str
    seed: int
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    invocations: list[ModelInvocation] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_opportunity_ids(self) -> "Run":
        ids = [item.id for item in self.opportunities]
        if len(ids) != len(set(ids)):
            raise ValueError("opportunity IDs must be unique within a run")
        return self
