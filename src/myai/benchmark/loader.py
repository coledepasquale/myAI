"""Loading a benchmark pack from outside the public repository.

The public repo must never contain real answer keys, so scoring code depends on
a loader contract rather than on committed data. The default location is the
git-ignored ``benchmarks/private/`` directory; ``MYAI_BENCHMARK_PACK`` overrides
it for a pack kept in a private repo or secure artifact store.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from myai.benchmark.schema import BenchmarkPack

PACK_ENV_VAR = "MYAI_BENCHMARK_PACK"
PACK_FILENAME = "pack.json"


class BenchmarkPackLoader(Protocol):
    def load(self) -> BenchmarkPack:
        """Return a validated benchmark pack."""
        ...


class FilesystemPackLoader:
    """Load ``pack.json`` from a directory, or from an explicit file path."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    def pack_file(self) -> Path:
        return self.path / PACK_FILENAME if self.path.is_dir() else self.path

    def load(self) -> BenchmarkPack:
        pack_file = self.pack_file
        if not pack_file.is_file():
            raise FileNotFoundError(
                f"no benchmark pack at {pack_file}. Author a private pack there, or set "
                f"{PACK_ENV_VAR} to the pack location."
            )
        return BenchmarkPack.model_validate_json(pack_file.read_text())


def default_pack_path(repo_root: Path) -> Path:
    override = os.environ.get(PACK_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser()
    return repo_root / "benchmarks" / "private"


def load_default_pack(repo_root: Path) -> BenchmarkPack:
    return FilesystemPackLoader(default_pack_path(repo_root)).load()
