from __future__ import annotations

import hashlib
import json
from pydantic import BaseModel, Field

from myai.domain import Opportunity
from myai.fixtures import CompanyFixture
from myai.model_gateway import ModelRequest, StructuredModel


class BaselineOutput(BaseModel):
    opportunities: list[Opportunity] = Field(default_factory=list)


BASELINE_SYSTEM = """You are evaluating a company for AI/software modernization opportunities.
Use only the evidence supplied. Rank opportunities by expected business value, confidence, feasibility,
and implementation cost. Every opportunity must cite at least one evidence ID. Expose assumptions instead
of silently inventing facts. Prefer bounded, measurable interventions over vague transformation advice.
"""


def _stable_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_baseline_request(fixture: CompanyFixture, model: str) -> ModelRequest:
    context = {
        "company": fixture.company(),
        "evidence": [item.model_dump(mode="json") for item in fixture.evidence()],
    }
    user = json.dumps(context, indent=2, sort_keys=True)
    return ModelRequest(
        system=BASELINE_SYSTEM,
        user=user,
        model=model,
        prompt_version="baseline-v0.1",
        temperature=0.0,
    )


def run_baseline(
    fixture: CompanyFixture,
    gateway: StructuredModel,
    model: str,
) -> BaselineOutput:
    request = build_baseline_request(fixture, model)
    result = gateway.generate(request, BaselineOutput)
    return result.value


def baseline_input_hash(fixture: CompanyFixture, model: str) -> str:
    request = build_baseline_request(fixture, model)
    return _stable_hash(request.system + "\n" + request.user)
