from __future__ import annotations

import json
from pathlib import Path

from myai.domain import Evidence


class CompanyFixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def company(self) -> dict[str, object]:
        return json.loads((self.root / "company.json").read_text())

    def evidence(self) -> list[Evidence]:
        payload = json.loads((self.root / "evidence.json").read_text())
        return [Evidence.model_validate(item) for item in payload]


def northstar_fixture(repo_root: Path | None = None) -> CompanyFixture:
    root = repo_root or Path.cwd()
    return CompanyFixture(root / "environments" / "northstar")
