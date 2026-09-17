"""Deterministic mapping from model prose to benchmark opportunity categories.

Scoring must be reproducible months later without a second LLM in the loop, so
classification is intentionally a transparent keyword rule rather than a model
call. Rules come from the benchmark pack; this module stays environment-neutral.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from myai.benchmark.schema import OpportunityCategoryRule
from myai.domain import Opportunity


def opportunity_text(opportunity: Opportunity) -> str:
    parts = [opportunity.title, opportunity.problem, opportunity.proposed_change]
    parts.extend(assumption.statement for assumption in opportunity.assumptions)
    return " ".join(parts).lower()


def match_category(
    opportunity: Opportunity,
    rules: Sequence[OpportunityCategoryRule],
) -> str | None:
    """Return the best-matching category ID, or None when nothing matches.

    Ties break on the lexicographically smallest category ID so that a given
    output always scores identically.
    """
    text = opportunity_text(opportunity)
    best_id: str | None = None
    best_hits = 0
    for rule in sorted(rules, key=lambda item: item.category_id):
        hits = sum(1 for keyword in set(rule.keywords) if keyword in text)
        if hits > best_hits:
            best_id, best_hits = rule.category_id, hits
    return best_id


def predicted_category_order(
    opportunities: Iterable[Opportunity],
    rules: Sequence[OpportunityCategoryRule],
) -> list[str]:
    """Categories in the order the model ranked them, first occurrence winning."""
    ordered: list[str] = []
    for opportunity in opportunities:
        category = match_category(opportunity, rules)
        if category is not None and category not in ordered:
            ordered.append(category)
    return ordered
