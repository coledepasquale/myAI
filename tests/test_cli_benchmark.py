import json
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from myai.cli import app

TOY_PACK = Path(__file__).parent / "data" / "toy_pack"
runner = CliRunner()


def test_validate_summarizes_a_pack_without_revealing_answers() -> None:
    result = runner.invoke(
        app, ["benchmark-validate", "--pack", str(TOY_PACK), "--allow-tracked"]
    )

    assert result.exit_code == 0, result.output
    assert "toy-v1" in result.output
    assert "toy-001" in result.output
    # The hidden ranking, decoys, and value bands must never reach the terminal.
    assert "alpha_automation" not in result.output
    assert "delta_decoy" not in result.output
    assert "Alpha is genuinely the largest win" not in result.output


def test_validate_reports_a_missing_pack() -> None:
    result = runner.invoke(app, ["benchmark-validate", "--pack", "/nonexistent/pack"])

    assert result.exit_code == 2
    assert "no benchmark pack" in result.output


def test_validate_rejects_an_incomplete_pack(tmp_path: Path) -> None:
    payload = json.loads((TOY_PACK / "pack.json").read_text())
    payload["answers"] = payload["answers"][:1]
    (tmp_path / "pack.json").write_text(json.dumps(payload))

    result = runner.invoke(app, ["benchmark-validate", "--pack", str(tmp_path)])

    assert result.exit_code == 1
    assert "invalid" in result.output.lower()


def test_validate_refuses_a_git_tracked_pack(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy(TOY_PACK / "pack.json", tmp_path / "pack.json")
    subprocess.run(["git", "-C", str(tmp_path), "add", "pack.json"], check=True)

    result = runner.invoke(app, ["benchmark-validate", "--pack", str(tmp_path)])

    assert result.exit_code == 3
    assert "tracked by Git" in result.output
