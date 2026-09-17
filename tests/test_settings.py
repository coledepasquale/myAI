from pydantic import SecretStr

from myai.settings import Settings


def test_settings_normalize_anthropic_workspace_id() -> None:
    settings = Settings(
        anthropic_api_key=SecretStr("test-key"),
        anthropic_workspace_id="  wrkspc_test  ",
    )

    assert settings.require_anthropic_api_key() == "test-key"
    assert settings.optional_anthropic_workspace_id() == "wrkspc_test"


def test_workspace_id_is_optional_for_scoped_keys() -> None:
    settings = Settings(anthropic_api_key=SecretStr("test-key"))

    assert settings.optional_anthropic_workspace_id() is None
