from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from myai.domain import Evidence

_COMPANY_ADAPTER = TypeAdapter(dict[str, object])
_EVIDENCE_ADAPTER = TypeAdapter(list[Evidence])


class CompanyFixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def company(self) -> dict[str, object]:
        return _COMPANY_ADAPTER.validate_json((self.root / "company.json").read_text())

    def evidence(self) -> list[Evidence]:
        return _EVIDENCE_ADAPTER.validate_json((self.root / "evidence.json").read_text())


def northstar_fixture(repo_root: Path | None = None) -> CompanyFixture:
    root = repo_root or Path.cwd()
    return CompanyFixture(root / "environments" / "northstar")
