from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field

from myai.domain import Evidence, Opportunity
from myai.fixtures import CompanyFixture
from myai.model_gateway import ModelRequest, ModelResult, StructuredModel


class BaselineOutput(BaseModel):
    opportunities: list[Opportunity] = Field(default_factory=list)


BASELINE_SYSTEM = (
    "You are evaluating a company for AI/software modernization opportunities.\n"
    "Use only the evidence supplied. Rank opportunities by expected business value, "
    "confidence, feasibility, and implementation cost. Every opportunity must cite at "
    "least one evidence ID. Expose assumptions instead of silently inventing facts. "
    "Prefer bounded, measurable interventions over vague transformation advice."
)


def _stable_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_context_request(
    company: dict[str, Any],
    evidence: list[Evidence],
    model: str,
) -> ModelRequest:
    """Build the frozen baseline-v0.1 request from raw observable context.

    This is the only place observable context is serialized for a model, so it
    is also the contamination boundary: it accepts company + evidence and
    nothing else — a hidden answer key has no path into the prompt.
    """
    context = {
        "company": company,
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    user = json.dumps(context, indent=2, sort_keys=True)
    return ModelRequest(
        system=BASELINE_SYSTEM,
        user=user,
        model=model,
        prompt_version="baseline-v0.1",
        max_output_tokens=8192,
    )


def build_baseline_request(fixture: CompanyFixture, model: str) -> ModelRequest:
    return build_context_request(fixture.company(), fixture.evidence(), model)


def request_input_hash(request: ModelRequest) -> str:
    return _stable_hash(request.system + "\n" + request.user)


def run_baseline_result(
    fixture: CompanyFixture,
    gateway: StructuredModel,
    model: str,
) -> ModelResult[BaselineOutput]:
    request = build_baseline_request(fixture, model)
    return gateway.generate(request, BaselineOutput)


def run_baseline(
    fixture: CompanyFixture,
    gateway: StructuredModel,
    model: str,
) -> BaselineOutput:
    return run_baseline_result(fixture, gateway, model).value


def baseline_input_hash(fixture: CompanyFixture, model: str) -> str:
    return request_input_hash(build_baseline_request(fixture, model))
