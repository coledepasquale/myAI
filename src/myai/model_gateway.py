from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class ModelRequest(BaseModel):
    system: str
    user: str
    model: str
    prompt_version: str
    max_output_tokens: int = Field(default=8192, ge=1)


class ModelResult[T: BaseModel](BaseModel):
    value: T
    provider: str
    model: str
    raw_text: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None


class StructuredModel(Protocol):
    provider_name: str

    def generate[T: BaseModel](
        self,
        request: ModelRequest,
        schema: type[T],
    ) -> ModelResult[T]:
        """Generate a schema-constrained result.

        Provider adapters own provider/model-specific request behavior. Domain code
        should not assume that sampling or reasoning parameters are portable.
        """
        ...
