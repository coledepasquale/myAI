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

# v0.2 adds an explicit value-discipline policy to the same one-shot control. It
# deliberately contains no environment-specific numbers: it teaches abstention and
# assumption disclosure, not this benchmark's hidden parameters.
BASELINE_SYSTEM_V02 = BASELINE_SYSTEM + (
    "\n\nValue discipline:\n"
    "- Provide \"annual_value_usd\" ONLY when the evidence supports all three of: how "
    "often the work happens (volume), how long it takes (time per unit), and who "
    "performs it (so a labor cost can be applied). If any of the three is missing, or "
    "two evidence records contradict each other about it, set \"annual_value_usd\" to "
    "null and state in the assumptions exactly which measurement is missing or "
    "conflicted.\n"
    "- When you do provide a value, show the arithmetic in the assumptions: cite the "
    "volume and time evidence, state the fully loaded hourly labor rate you assumed "
    "for that role (use standard published rates; disclose the number), and state the "
    "share of the observed labor you assume software can realistically remove.\n"
    "- Treat \"confidence\" as a calibrated probability that the opportunity is truly "
    "among this company's highest-value options given only this evidence — not as "
    "enthusiasm. If you abstained from a value, confidence should usually be low.\n"
    "- Never let an impressive-sounding initiative outrank one with better-evidenced "
    "value."
)

PROMPT_VERSIONS: dict[str, str] = {
    "baseline-v0.1": BASELINE_SYSTEM,
    "baseline-v0.2": BASELINE_SYSTEM_V02,
}


def _stable_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_context_request(
    company: dict[str, Any],
    evidence: list[Evidence],
    model: str,
    effort: str = "high",
    prompt_version: str = "baseline-v0.1",
) -> ModelRequest:
    """Build the frozen baseline-v0.1 request from raw observable context.

    This is the only place observable context is serialized for a model, so it
    is also the contamination boundary: it accepts company + evidence and
    nothing else — a hidden answer key has no path into the prompt.
    """
    try:
        system = PROMPT_VERSIONS[prompt_version]
    except KeyError as exc:
        raise ValueError(
            f"unknown prompt version {prompt_version!r}; known: {sorted(PROMPT_VERSIONS)}"
        ) from exc
    context = {
        "company": company,
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    user = json.dumps(context, indent=2, sort_keys=True)
    return ModelRequest(
        system=system,
        user=user,
        model=model,
        prompt_version=prompt_version,
        max_output_tokens=8192,
        effort=effort,
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
