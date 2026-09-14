from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelRequest(BaseModel):
    system: str
    user: str
    model: str
    prompt_version: str
    temperature: float = 0.0


class ModelResult(BaseModel, Generic[T]):
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

    def generate(self, request: ModelRequest, schema: type[T]) -> ModelResult[T]:
        """Generate a schema-constrained result.

        Provider adapters must implement this boundary. Domain code must not import
        provider SDKs directly.
        """
        ...
