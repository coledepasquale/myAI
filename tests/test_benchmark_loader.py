import shutil
from pathlib import Path

import pytest

from myai.benchmark import FilesystemPackLoader, default_pack_path, load_default_pack
from myai.benchmark.loader import PACK_ENV_VAR

TOY_PACK = Path(__file__).parent / "data" / "toy_pack"


def test_default_pack_path_is_the_gitignored_private_directory(tmp_path: Path) -> None:
    assert default_pack_path(tmp_path) == tmp_path / "benchmarks" / "private"


def test_env_var_overrides_default_pack_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(PACK_ENV_VAR, str(TOY_PACK))
    assert default_pack_path(tmp_path) == TOY_PACK


def test_missing_pack_raises_an_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=PACK_ENV_VAR):
        FilesystemPackLoader(tmp_path).load()


def test_loader_accepts_a_directory_or_an_explicit_file() -> None:
    from_dir = FilesystemPackLoader(TOY_PACK).load()
    from_file = FilesystemPackLoader(TOY_PACK / "pack.json").load()
    assert from_dir.pack_hash == from_file.pack_hash


def test_load_default_pack_reads_the_private_directory(tmp_path: Path) -> None:
    private = tmp_path / "benchmarks" / "private"
    private.mkdir(parents=True)
    shutil.copy(TOY_PACK / "pack.json", private / "pack.json")

    pack = load_default_pack(tmp_path)

    assert pack.pack_version == "toy-v1"


def test_private_pack_directory_stays_out_of_version_control() -> None:
    ignored = (Path(__file__).parents[1] / ".gitignore").read_text().splitlines()
    assert "benchmarks/private/" in ignored
