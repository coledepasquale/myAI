from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: SecretStr | None = None
    anthropic_workspace_id: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def require_anthropic_api_key(self) -> str:
        if self.anthropic_api_key is None:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured. Put it in the local .env file."
            )
        value = self.anthropic_api_key.get_secret_value().strip()
        if not value:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is empty. Put the key in the local .env file."
            )
        return value

    def optional_anthropic_workspace_id(self) -> str | None:
        if self.anthropic_workspace_id is None:
            return None
        value = self.anthropic_workspace_id.strip()
        return value or None
