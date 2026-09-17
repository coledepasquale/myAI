from __future__ import annotations

from typing import Any, cast

import pytest

from myai.settings import Settings


@pytest.fixture(autouse=True)
def isolate_local_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests independent of the developer's local .env and shell environment.

    Without this, a populated local .env silently leaks real credentials into
    Settings() and makes credential tests pass or fail per machine.
    """
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_WORKSPACE_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(cast(dict[str, Any], Settings.model_config), "env_file", None)
