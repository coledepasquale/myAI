"""Typed benchmark schemas.

This module is public. It defines the *shape* of benchmark material, never the
material itself. Real Northstar answer keys live in a git-ignored private pack
(see ``benchmarks/README.md``).

The observable half (:class:`BenchmarkCase`) and the hidden half
(:class:`CaseAnswerKey`) are deliberately separate types so that runtime code
cannot accidentally serialize answers into a model prompt.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field, model_validator

from myai.domain import Evidence

DEFAULT_APPROVAL_KEYWORDS: tuple[str, ...] = (
    "approval",
    "approve",
    "approver",
    "human review",
    "human-in-the-loop",
    "reviewed by",
    "sign-off",
    "sign off",
)


class OpportunityCategoryRule(BaseModel):
    """Deterministic mapping from free-text opportunity prose to a category ID.

    Rules are pack data rather than code so that public scoring logic stays
    generic and no environment-specific taxonomy needs to be committed.
    """

    category_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_keywords(self) -> OpportunityCategoryRule:
        normalized = [keyword.strip().lower() for keyword in self.keywords]
        if any(not keyword for keyword in normalized):
            raise ValueError(f"category {self.category_id} has an empty keyword")
        object.__setattr__(self, "keywords", normalized)
        return self


class ValueBand(BaseModel):
    """Hidden annual-value range considered defensible for a category."""

    low_usd: float = Field(ge=0)
    high_usd: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered(self) -> ValueBand:
        if self.low_usd > self.high_usd:
            raise ValueError("low_usd must not exceed high_usd")
        return self

    @property
    def midpoint_usd(self) -> float:
        return (self.low_usd + self.high_usd) / 2.0

    def contains(self, value: float) -> bool:
        return self.low_usd <= value <= self.high_usd


class BenchmarkCase(BaseModel):
    """Everything a model or the myAI system is allowed to observe for one case."""

    case_id: str = Field(min_length=1)
    variant_id: str = Field(min_length=1)
    company: dict[str, Any]
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_evidence_ids(self) -> BenchmarkCase:
        ids = [item.id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError(f"case {self.case_id} has duplicate evidence IDs")
        return self


class CaseAnswerKey(BaseModel):
    """Hidden truth for one case. Never place this in model context."""

    case_id: str = Field(min_length=1)
    true_ranking: list[str] = Field(min_length=1)
    high_value_categories: list[str] = Field(min_length=1)
    decoy_categories: list[str] = Field(default_factory=list)
    insufficient_evidence_categories: list[str] = Field(default_factory=list)
    value_bands: dict[str, ValueBand] = Field(default_factory=dict)
    required_policy_keywords: list[str] = Field(default_factory=list)
    prohibited_action_keywords: list[str] = Field(default_factory=list)
    approval_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_APPROVAL_KEYWORDS))
    notes: str | None = None

    @model_validator(mode="after")
    def internally_consistent(self) -> CaseAnswerKey:
        if len(self.true_ranking) != len(set(self.true_ranking)):
            raise ValueError(f"case {self.case_id} repeats a category in true_ranking")
        ranked = set(self.true_ranking)
        missing = sorted(set(self.high_value_categories) - ranked)
        if missing:
            raise ValueError(f"case {self.case_id} high_value categories not ranked: {missing}")
        overlap = sorted(set(self.high_value_categories) & set(self.decoy_categories))
        if overlap:
            raise ValueError(
                f"case {self.case_id} marks categories both high-value and decoy: {overlap}"
            )
        banded = sorted(set(self.insufficient_evidence_categories) & set(self.value_bands))
        if banded:
            raise ValueError(
                f"case {self.case_id} gives value bands to "
                f"insufficient-evidence categories: {banded}"
            )
        return self

    @property
    def true_rank_index(self) -> dict[str, int]:
        return {category: index for index, category in enumerate(self.true_ranking)}


class BenchmarkPack(BaseModel):
    """A versioned, hashable bundle of cases, answers, and category rules."""

    pack_version: str = Field(min_length=1)
    category_rules: list[OpportunityCategoryRule] = Field(min_length=1)
    cases: list[BenchmarkCase] = Field(min_length=1)
    answers: list[CaseAnswerKey] = Field(min_length=1)

    @model_validator(mode="after")
    def cases_and_answers_align(self) -> BenchmarkPack:
        case_ids = [case.case_id for case in self.cases]
        answer_ids = [answer.case_id for answer in self.answers]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("duplicate case IDs in pack")
        if len(answer_ids) != len(set(answer_ids)):
            raise ValueError("duplicate answer IDs in pack")
        if set(case_ids) != set(answer_ids):
            unanswered = sorted(set(case_ids) - set(answer_ids))
            orphaned = sorted(set(answer_ids) - set(case_ids))
            raise ValueError(
                f"pack is incomplete (cases without answers: {unanswered}; "
                f"answers without cases: {orphaned})"
            )

        rule_ids = [rule.category_id for rule in self.category_rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("duplicate category IDs in pack")
        known = set(rule_ids)
        for answer in self.answers:
            referenced = (
                set(answer.true_ranking)
                | set(answer.decoy_categories)
                | set(answer.insufficient_evidence_categories)
                | set(answer.value_bands)
            )
            unknown = sorted(referenced - known)
            if unknown:
                raise ValueError(f"case {answer.case_id} references unknown categories: {unknown}")
        return self

    @property
    def pack_hash(self) -> str:
        """Stable digest so results can be tied to one frozen target."""
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def observable_cases(self) -> list[BenchmarkCase]:
        """The only pack content that may reach a model prompt."""
        return list(self.cases)

    def case(self, case_id: str) -> BenchmarkCase:
        for item in self.cases:
            if item.case_id == case_id:
                return item
        raise KeyError(f"unknown benchmark case: {case_id}")

    def answer(self, case_id: str) -> CaseAnswerKey:
        for item in self.answers:
            if item.case_id == case_id:
                return item
        raise KeyError(f"unknown benchmark answer: {case_id}")
