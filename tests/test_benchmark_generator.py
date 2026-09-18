import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from myai.benchmark import BenchmarkPack
from myai.benchmark.generator import (
    ARCHETYPES,
    DASHBOARD,
    POLICY,
    PROCUREMENT,
    QUOTE,
    SUPPORT,
    GeneratorParams,
    PackManifest,
    generate_pack,
    load_params,
)
from myai.cli import app

REPO_ROOT = Path(__file__).parents[1]
runner = CliRunner()


@pytest.fixture(scope="module")
def company() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (REPO_ROOT / "environments" / "northstar" / "company.json").read_text()
    )
    return loaded


@pytest.fixture(scope="module")
def generated(company: dict[str, Any]) -> tuple[BenchmarkPack, PackManifest]:
    return generate_pack(GeneratorParams(seed=20260918, case_count=24), company)


def test_generation_is_deterministic_and_seed_sensitive(company: dict[str, Any]) -> None:
    first, _ = generate_pack(GeneratorParams(seed=1, case_count=8), company)
    second, _ = generate_pack(GeneratorParams(seed=1, case_count=8), company)
    third, _ = generate_pack(GeneratorParams(seed=2, case_count=8), company)

    assert first.pack_hash == second.pack_hash
    assert first.pack_hash != third.pack_hash


def test_missing_seed_is_rejected_with_guidance() -> None:
    with pytest.raises(ValueError, match="seed"):
        GeneratorParams(seed=None).require_seed()


def test_generated_pack_is_schema_valid_and_round_trips(
    generated: tuple[BenchmarkPack, PackManifest],
) -> None:
    pack, _ = generated
    reloaded = BenchmarkPack.model_validate_json(pack.model_dump_json())
    assert reloaded.pack_hash == pack.pack_hash
    assert len(pack.cases) == 24


def test_every_archetype_appears(generated: tuple[BenchmarkPack, PackManifest]) -> None:
    _, manifest = generated
    seen = {case.archetype for case in manifest.cases}
    assert seen == set(ARCHETYPES)


def test_ranking_follows_computed_truth(generated: tuple[BenchmarkPack, PackManifest]) -> None:
    pack, manifest = generated
    for row in manifest.cases:
        answer = pack.answer(row.case_id)
        sized = {key: value for key, value in row.truth_usd.items() if value is not None}
        expected_head = sorted(sized, key=lambda key: -sized[key])
        assert answer.true_ranking[: len(expected_head)] == expected_head
        # Unsizeable categories rank behind every sized one and get no value band.
        tail = answer.true_ranking[len(expected_head) :]
        assert set(tail) == set(answer.insufficient_evidence_categories)
        assert not set(tail) & set(answer.value_bands)


def test_winner_evidence_contains_its_numbers(
    generated: tuple[BenchmarkPack, PackManifest],
) -> None:
    pack, manifest = generated
    for row in manifest.cases:
        answer = pack.answer(row.case_id)
        winner = answer.true_ranking[0]
        band = answer.value_bands[winner]
        truth = row.truth_usd[winner]
        assert truth is not None
        assert band.low_usd <= truth <= band.high_usd
        # The winning area's arithmetic must be reproducible from displayed values,
        # which the generator guarantees by recomputing truth after rounding.
        assert any(winner in line for line in row.arithmetic)


def test_archetype_specific_answer_properties(
    generated: tuple[BenchmarkPack, PackManifest],
) -> None:
    pack, manifest = generated
    for row in manifest.cases:
        answer = pack.answer(row.case_id)
        if row.archetype == "decoy_prominent":
            assert answer.decoy_categories == [DASHBOARD]
            assert DASHBOARD in answer.true_ranking
            assert DASHBOARD not in answer.high_value_categories
        if row.archetype == "policy_trap":
            assert answer.prohibited_action_keywords
            assert "approval" in answer.required_policy_keywords
        if row.archetype == "contradictory_support":
            assert SUPPORT in answer.insufficient_evidence_categories
        if row.archetype == "insufficient_policy":
            assert POLICY in answer.insufficient_evidence_categories
        assert PROCUREMENT in answer.insufficient_evidence_categories


def test_variant_ids_do_not_leak_the_archetype(
    generated: tuple[BenchmarkPack, PackManifest],
) -> None:
    pack, _ = generated
    for case in pack.observable_cases():
        assert case.variant_id == f"v{case.case_id.split('-')[1]}"
        for archetype in ARCHETYPES:
            assert archetype not in case.variant_id


def test_dominant_winners_hold_a_margin(generated: tuple[BenchmarkPack, PackManifest]) -> None:
    _, manifest = generated
    for row in manifest.cases:
        sized = sorted(
            (value for value in row.truth_usd.values() if value is not None), reverse=True
        )
        if row.archetype.endswith("_dominant") and len(sized) >= 2:
            assert sized[0] >= sized[1] * 1.08
        if row.archetype == "near_tie":
            assert 0.82 <= sized[1] / sized[0] < 1.0


def test_quote_value_matches_displayed_evidence_numbers(
    company: dict[str, Any],
) -> None:
    params = GeneratorParams(seed=99, case_count=8)
    pack, manifest = generate_pack(params, company)
    row = next(item for item in manifest.cases if item.archetype == "quote_dominant")
    case = pack.case(row.case_id)
    texts = " ".join(item.content for item in case.evidence)

    quote_truth = row.truth_usd[QUOTE]
    assert quote_truth is not None
    line = next(line for line in row.arithmetic if line.startswith(QUOTE))
    volume = int(line.split(":")[1].split("/yr")[0].strip().replace(",", ""))
    minutes = float(line.split(" x ")[1].split(" min")[0])
    rate = params.labor_rates_usd_per_hour.sales_rep
    frac = params.automatable_fraction[QUOTE]

    assert f"{volume:,}" in texts and str(minutes) in texts
    assert quote_truth == pytest.approx(volume * minutes / 60.0 * rate * frac)


def test_cli_generate_writes_pack_and_manifest(tmp_path: Path) -> None:
    params_file = tmp_path / "params.json"
    payload = json.loads((REPO_ROOT / "benchmarks" / "params.example.json").read_text())
    payload["seed"] = 12345
    payload["case_count"] = 8
    params_file.write_text(json.dumps(payload))
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            "benchmark-generate",
            "--params", str(params_file),
            "--out", str(out_dir),
            "--root", str(REPO_ROOT),
        ],
    )

    assert result.exit_code == 0, result.output
    pack = BenchmarkPack.model_validate_json((out_dir / "pack.json").read_text())
    assert pack.pack_hash in result.output
    assert (out_dir / "manifest.json").exists()
    # The terminal summary must not reveal answers.
    assert "true_ranking" not in result.output
    assert "quote_automation" not in result.output


def test_cli_generate_refuses_unignored_output_inside_repo(tmp_path: Path) -> None:
    params_file = tmp_path / "params.json"
    payload = json.loads((REPO_ROOT / "benchmarks" / "params.example.json").read_text())
    payload["seed"] = 12345
    params_file.write_text(json.dumps(payload))
    forbidden = REPO_ROOT / "docs" / "leaked-pack"

    result = runner.invoke(
        app,
        [
            "benchmark-generate",
            "--params", str(params_file),
            "--out", str(forbidden),
            "--root", str(REPO_ROOT),
        ],
    )

    assert result.exit_code == 3
    assert "SECURITY" in result.output
    assert not forbidden.exists()


def test_cli_generate_reports_missing_params(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["benchmark-generate", "--params", str(tmp_path / "missing.json"),
         "--out", str(tmp_path), "--root", str(REPO_ROOT)],
    )

    assert result.exit_code == 2
    assert "params.example.json" in result.output


def test_example_params_file_is_valid_apart_from_seed() -> None:
    text = (REPO_ROOT / "benchmarks" / "params.example.json").read_text()
    params = load_params(text)
    assert params.seed is None
    with pytest.raises(ValueError):
        params.require_seed()
