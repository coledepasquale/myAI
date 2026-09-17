from __future__ import annotations

from time import perf_counter

from anthropic import Anthropic
from pydantic import BaseModel

from myai.model_gateway import ModelRequest, ModelResult

# Standard Claude API pricing captured 2026-09-17. Keep this table explicit so
# historical run artifacts remain interpretable if provider pricing changes.
_PRICING_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    pricing = _PRICING_PER_MILLION_TOKENS.get(model)
    if pricing is None:
        return None
    input_rate, output_rate = pricing
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


class AnthropicStructuredModel:
    provider_name = "anthropic"

    def __init__(self, api_key: str, workspace_id: str | None = None) -> None:
        default_headers = (
            {"anthropic-workspace-id": workspace_id} if workspace_id is not None else None
        )
        self._client = Anthropic(
            api_key=api_key,
            timeout=120.0,
            max_retries=2,
            default_headers=default_headers,
        )

    def generate[T: BaseModel](
        self,
        request: ModelRequest,
        schema: type[T],
    ) -> ModelResult[T]:
        started = perf_counter()
        response = self._client.messages.parse(
            model=request.model,
            max_tokens=request.max_output_tokens,
            system=request.system,
            messages=[{"role": "user", "content": request.user}],
            output_format=schema,
        )
        latency_ms = round((perf_counter() - started) * 1000)

        parsed = response.parsed_output
        if parsed is None:
            raise RuntimeError("Anthropic returned no parsed structured output")

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        return ModelResult[T](
            value=parsed,
            provider=self.provider_name,
            model=response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=estimate_cost_usd(response.model, input_tokens, output_tokens),
        )
