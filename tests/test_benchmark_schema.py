from pathlib import Path

import pytest
from pydantic import ValidationError

from myai.benchmark import BenchmarkPack, CaseAnswerKey, FilesystemPackLoader, ValueBand

TOY_PACK = Path(__file__).parent / "data" / "toy_pack"


def load_toy_pack() -> BenchmarkPack:
    return FilesystemPackLoader(TOY_PACK).load()


def test_pack_hash_is_stable_and_content_sensitive() -> None:
    pack = load_toy_pack()
    assert pack.pack_hash == load_toy_pack().pack_hash
    assert len(pack.pack_hash) == 64

    renamed = pack.model_copy(update={"pack_version": "toy-v2"})
    assert renamed.pack_hash != pack.pack_hash


def test_pack_accessors_separate_observable_from_hidden() -> None:
    pack = load_toy_pack()
    case = pack.case("toy-001")
    answer = pack.answer("toy-001")

    observable_fields = set(case.model_dump().keys())
    assert observable_fields == {"case_id", "variant_id", "company", "evidence"}
    assert "true_ranking" not in observable_fields
    assert answer.true_ranking[0] == "alpha_automation"

    with pytest.raises(KeyError):
        pack.case("missing")


def test_value_band_rejects_inverted_range() -> None:
    with pytest.raises(ValidationError):
        ValueBand(low_usd=100.0, high_usd=50.0)


def test_answer_key_rejects_unranked_high_value_category() -> None:
    with pytest.raises(ValidationError):
        CaseAnswerKey(
            case_id="bad",
            true_ranking=["a"],
            high_value_categories=["b"],
        )


def test_answer_key_rejects_category_that_is_both_high_value_and_decoy() -> None:
    with pytest.raises(ValidationError):
        CaseAnswerKey(
            case_id="bad",
            true_ranking=["a"],
            high_value_categories=["a"],
            decoy_categories=["a"],
        )


def test_answer_key_rejects_value_band_on_unsizeable_category() -> None:
    with pytest.raises(ValidationError):
        CaseAnswerKey(
            case_id="bad",
            true_ranking=["a"],
            high_value_categories=["a"],
            insufficient_evidence_categories=["a"],
            value_bands={"a": ValueBand(low_usd=1.0, high_usd=2.0)},
        )


def test_pack_rejects_case_without_answer() -> None:
    pack = load_toy_pack()
    payload = pack.model_dump(mode="json")
    payload["answers"] = payload["answers"][:1]

    with pytest.raises(ValidationError, match="cases without answers"):
        BenchmarkPack.model_validate(payload)


def test_pack_rejects_answer_referencing_unknown_category() -> None:
    pack = load_toy_pack()
    payload = pack.model_dump(mode="json")
    payload["answers"][0]["true_ranking"].append("not_a_category")

    with pytest.raises(ValidationError, match="unknown categories"):
        BenchmarkPack.model_validate(payload)
