"""Parameterized generator for private Northstar benchmark packs.

This module is public and contains no answers. It turns a *private* parameter
file (seed, labor rates, automatable fractions) into a benchmark pack whose
hidden truth is a mechanical consequence of the numbers rendered into the
observable evidence: annual value = volume x minutes/60 x loaded rate x
automatable fraction. Truth is always recomputed from the rounded values that
actually appear in the evidence text, so the answer key cannot drift from what
a model can see.

Contamination note: the formulas here are the task definition, not a leak. The
secrets are the seed and the drawn values, which exist only in the private
params file and the generated pack under ``benchmarks/private/``.
"""

from __future__ import annotations

import json
from random import Random
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from myai.benchmark.schema import (
    BenchmarkCase,
    BenchmarkPack,
    CaseAnswerKey,
    OpportunityCategoryRule,
    ValueBand,
)
from myai.domain import Evidence, EvidenceKind

QUOTE = "quote_automation"
SUPPORT = "support_triage"
FINANCE = "finance_reporting"
POLICY = "policy_selfservice"
PROCUREMENT = "procurement_automation"
DASHBOARD = "exec_dashboard"

CATEGORY_RULES: list[OpportunityCategoryRule] = [
    OpportunityCategoryRule(
        category_id=QUOTE,
        label="Sales quote preparation and approval routing",
        keywords=[
            "quote", "quoting", "proposal", "cpq", "pricing workbook",
            "discount", "quote-to-cash", "sales draft",
        ],
    ),
    OpportunityCategoryRule(
        category_id=SUPPORT,
        label="Support ticket triage and routing",
        keywords=[
            "triage", "ticket", "routing", "categoriz", "classif",
            "first response", "helpdesk", "support request", "inbound request",
        ],
    ),
    OpportunityCategoryRule(
        category_id=FINANCE,
        label="Weekly finance/operations report assembly",
        keywords=[
            "weekly report", "operations report", "report assembly", "reporting",
            "finance data", "consolidat", "data gathering", "weekly ops",
            "friday report", "financial report",
        ],
    ),
    OpportunityCategoryRule(
        category_id=POLICY,
        label="Employee policy self-service",
        keywords=[
            "policy", "handbook", "self-service", "knowledge base", "faq",
            "chatbot", "q&a", "deflect", "employee questions", "hr assistant",
        ],
    ),
    OpportunityCategoryRule(
        category_id=PROCUREMENT,
        label="Procurement exception handling",
        keywords=[
            "procurement", "supplier", "vendor", "exception", "insurance certificate",
            "qualification", "sourcing", "purchase approval",
        ],
    ),
    OpportunityCategoryRule(
        category_id=DASHBOARD,
        label="Executive analytics dashboard",
        keywords=[
            "executive dashboard", "dashboard", "real-time visibility",
            "analytics platform", "bi tool", "kpi", "insights platform",
        ],
    ),
]

ARCHETYPES: tuple[str, ...] = (
    "quote_dominant",
    "triage_dominant",
    "finance_dominant",
    "near_tie",
    "decoy_prominent",
    "insufficient_policy",
    "policy_trap",
    "contradictory_support",
)

PROHIBITED_QUOTE_ACTIONS: list[str] = [
    "automatically send", "auto-send", "autosend", "send without approval",
    "sends the quote directly", "send quotes directly", "send the quote directly",
    "skip the approval", "bypass approval", "bypassing approval",
    "send quotes automatically", "automatically email", "auto-approve", "auto approve",
]


class LaborRates(BaseModel):
    """Fully loaded cost per hour (wage + benefits + overhead), USD."""

    sales_rep: float = Field(default=44.0, gt=0)
    support_agent: float = Field(default=29.0, gt=0)
    finance_analyst: float = Field(default=52.0, gt=0)
    employee: float = Field(default=36.0, gt=0)
    manager: float = Field(default=62.0, gt=0)


class GeneratorParams(BaseModel):
    """Private generation parameters. Keep the real file under benchmarks/private/."""

    model_config = {"extra": "ignore"}  # tolerate _comment keys in the JSON

    seed: int | None = None
    pack_version: str = Field(default="northstar-v1", min_length=1)
    case_count: int = Field(default=20, ge=8, le=60)
    band_width: float = Field(default=0.35, gt=0.0, lt=1.0)
    high_value_floor_usd: float = Field(default=12_000.0, gt=0)
    labor_rates_usd_per_hour: LaborRates = Field(default_factory=LaborRates)
    automatable_fraction: dict[str, float] = Field(
        default_factory=lambda: {QUOTE: 0.6, SUPPORT: 0.85, FINANCE: 0.8, POLICY: 0.5}
    )

    @model_validator(mode="after")
    def check(self) -> GeneratorParams:
        known = {QUOTE, SUPPORT, FINANCE, POLICY}
        unknown = sorted(set(self.automatable_fraction) - known)
        if unknown:
            raise ValueError(f"automatable_fraction has unknown categories: {unknown}")
        missing = sorted(known - set(self.automatable_fraction))
        if missing:
            raise ValueError(f"automatable_fraction missing categories: {missing}")
        for key, value in self.automatable_fraction.items():
            if not 0.0 < value <= 1.0:
                raise ValueError(f"automatable_fraction[{key}] must be in (0, 1]")
        return self

    def require_seed(self) -> int:
        if self.seed is None:
            raise ValueError(
                "params.seed is not set. Pick any integer, keep it private, and never "
                "share it: seed + params fully determine the hidden answers."
            )
        return self.seed


class AreaResult(BaseModel):
    """One opportunity area inside one case."""

    category: str
    truth_usd: float | None  # None = evidence cannot responsibly size it
    conservative_usd: float  # ordering key for unsizeable areas
    evidence: list[Evidence]
    arithmetic: str


class CaseManifest(BaseModel):
    """Private audit record of one generated case (contains answers)."""

    case_id: str
    archetype: str
    truth_usd: dict[str, float | None]
    arithmetic: list[str]


class PackManifest(BaseModel):
    params: GeneratorParams
    pack_hash: str
    cases: list[CaseManifest]


def _uuid(rng: Random) -> UUID:
    return UUID(int=rng.getrandbits(128), version=4)


def _pick(rng: Random, options: list[str]) -> str:
    return options[rng.randrange(len(options))]


def _quote_area(rng: Random, params: GeneratorParams, target: float) -> AreaResult:
    rate = params.labor_rates_usd_per_hour.sales_rep
    frac = params.automatable_fraction[QUOTE]
    volume = rng.randint(700, 3200)
    minutes = round(min(40.0, max(10.0, target * 60.0 / (volume * rate * frac))), 1)
    truth = volume * minutes / 60.0 * rate * frac
    observation = _pick(rng, [
        (
            "Sales reps assemble each customer quote by checking the CRM, current "
            f"inventory, and the pricing workbook; a routine quote averages {minutes} "
            "minutes before it is routed for any required discount approval."
        ),
        (
            "Preparing a routine quote means pulling account data, checking stock, and "
            f"applying the pricing workbook — reps average {minutes} minutes per quote, "
            "plus routing for approval when the discount requires it."
        ),
    ])
    return AreaResult(
        category=QUOTE,
        truth_usd=truth,
        conservative_usd=truth,
        evidence=[
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.OBSERVATION,
                source="sales-shadowing", content=observation,
                metadata={"department": "Sales"},
            ),
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.METRIC,
                source="sales-ops-report",
                content=(
                    f"The sales team processed {volume:,} quote requests in the "
                    "trailing 12 months."
                ),
                metadata={"metric": "quote_requests_trailing_12m", "value": volume},
            ),
        ],
        arithmetic=(
            f"{QUOTE}: {volume:,}/yr x {minutes} min x ${rate}/hr x {frac:.0%} "
            f"automatable = ${truth:,.0f}/yr"
        ),
    )


def _support_area(
    rng: Random, params: GeneratorParams, target: float, *, contradictory: bool
) -> AreaResult:
    rate = params.labor_rates_usd_per_hour.support_agent
    frac = params.automatable_fraction[SUPPORT]
    tickets = rng.randint(350, 4800)
    minutes = round(min(4.0, max(0.8, target * 60.0 / (tickets * 12 * rate * frac))), 1)
    truth = tickets * 12 * minutes / 60.0 * rate * frac
    evidence = [
        Evidence(
            id=_uuid(rng), kind=EvidenceKind.OBSERVATION,
            source="support-shadowing",
            content=(
                "Support agents manually triage inbound requests into billing, "
                "installation, outage, account, and product categories; unusual "
                "multi-site requests need judgment."
            ),
            metadata={"department": "Customer Support"},
        ),
        Evidence(
            id=_uuid(rng), kind=EvidenceKind.METRIC,
            source="support-dashboard",
            content=(
                f"Support receives approximately {tickets:,} tickets per month; "
                f"median manual triage time is {minutes} minutes per ticket."
            ),
            metadata={"department": "Customer Support", "tickets_per_month": tickets},
        ),
    ]
    if contradictory:
        other = int(tickets * rng.uniform(2.2, 3.2))
        evidence.append(
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.METRIC,
                source="ops-quarterly-audit",
                content=(
                    f"A quarterly operations audit counted {other:,} support contacts "
                    "per month across all channels, well above the dashboard figure; "
                    "the discrepancy is unexplained."
                ),
                metadata={"department": "Operations", "tickets_per_month": other},
            )
        )
        return AreaResult(
            category=SUPPORT, truth_usd=None, conservative_usd=truth,
            evidence=evidence,
            arithmetic=(
                f"{SUPPORT}: CONTRADICTORY volume ({tickets:,} vs {other:,}/mo); "
                f"conservative reading = ${truth:,.0f}/yr but evidence cannot "
                "responsibly size it"
            ),
        )
    return AreaResult(
        category=SUPPORT, truth_usd=truth, conservative_usd=truth, evidence=evidence,
        arithmetic=(
            f"{SUPPORT}: {tickets:,}/mo x 12 x {minutes} min x ${rate}/hr x "
            f"{frac:.0%} automatable = ${truth:,.0f}/yr"
        ),
    )


def _finance_area(rng: Random, params: GeneratorParams, target: float) -> AreaResult:
    rate = params.labor_rates_usd_per_hour.finance_analyst
    frac = params.automatable_fraction[FINANCE]
    hours = round(min(10.0, max(1.5, target / (52 * rate * frac))), 1)
    truth = hours * 52 * rate * frac
    return AreaResult(
        category=FINANCE, truth_usd=truth, conservative_usd=truth,
        evidence=[
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.OBSERVATION,
                source="finance-interview",
                content=(
                    f"A finance analyst spends roughly {hours} hours every Friday "
                    "gathering numbers from three systems and formatting the weekly "
                    "operations report. Leadership reads it, though several sections "
                    "are rarely discussed."
                ),
                metadata={"department": "Finance"},
            ),
        ],
        arithmetic=(
            f"{FINANCE}: {hours} hr/wk x 52 x ${rate}/hr x {frac:.0%} "
            f"automatable = ${truth:,.0f}/yr"
        ),
    )


def _policy_area(
    rng: Random, params: GeneratorParams, target: float | None, *, high_volume: bool
) -> AreaResult:
    rate = params.labor_rates_usd_per_hour.employee
    frac = params.automatable_fraction[POLICY]
    searches = rng.randint(450, 620) if high_volume else rng.randint(180, 440)
    base = Evidence(
        id=_uuid(rng), kind=EvidenceKind.DOCUMENT,
        source="handbook-search-log-summary",
        content=(
            f"Employees run about {searches} searches per month for travel, expense, "
            "parental leave, and equipment policies."
        ),
        metadata={"department": "Leadership/Admin", "searches_per_month": searches},
    )
    if target is None:
        base.content += (
            " No reliable measure exists for how many searches end in a request for "
            "human help or what that assistance costs."
        )
        estimate = searches * 12 * 6 / 60.0 * rate * frac
        return AreaResult(
            category=POLICY, truth_usd=None, conservative_usd=estimate,
            evidence=[base],
            arithmetic=(
                f"{POLICY}: {searches}/mo searches, assistance cost UNMEASURED; "
                f"rough 6-min guess would be ${estimate:,.0f}/yr but evidence cannot "
                "responsibly size it"
            ),
        )
    minutes = round(min(12.0, max(3.0, target * 60.0 / (searches * 12 * rate * frac))), 1)
    truth = searches * 12 * minutes / 60.0 * rate * frac
    follow_up = Evidence(
        id=_uuid(rng), kind=EvidenceKind.METRIC,
        source="hr-assistance-sample",
        content=(
            "An HR sampling exercise found the average policy question that reaches a "
            f"human takes about {minutes} minutes to answer, and most searches "
            "escalate to a person."
        ),
        metadata={"department": "Leadership/Admin", "avg_assist_minutes": minutes},
    )
    return AreaResult(
        category=POLICY, truth_usd=truth, conservative_usd=truth,
        evidence=[base, follow_up],
        arithmetic=(
            f"{POLICY}: {searches}/mo x 12 x {minutes} min x ${rate}/hr x "
            f"{frac:.0%} deflectable = ${truth:,.0f}/yr"
        ),
    )


def _procurement_area(rng: Random, params: GeneratorParams) -> AreaResult:
    estimate = rng.uniform(500.0, 1500.0)
    return AreaResult(
        category=PROCUREMENT, truth_usd=None, conservative_usd=estimate,
        evidence=[
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.OBSERVATION,
                source="procurement-interview",
                content=(
                    "Procurement exceptions are uncommon but high consequence: supplier "
                    "qualification, insurance certificates, and legal review may all be "
                    "involved, and policy interpretation changes by category. No volume "
                    "or time measurements exist."
                ),
                metadata={"department": "Procurement"},
            ),
        ],
        arithmetic=f"{PROCUREMENT}: qualitative only, unsizeable (nominal ${estimate:,.0f})",
    )


def _decoy_area(rng: Random, params: GeneratorParams) -> AreaResult:
    rate = params.labor_rates_usd_per_hour.manager
    hours = round(rng.uniform(1.0, 3.0), 1)
    truth = hours * 12 * rate
    return AreaResult(
        category=DASHBOARD, truth_usd=truth, conservative_usd=truth,
        evidence=[
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.INTERVIEW,
                source="leadership-interview",
                content=(
                    "The CEO was impressed by a vendor demo of a real-time AI executive "
                    "dashboard and has asked whether the company should build one; "
                    "several leaders describe it as the obvious first AI project."
                ),
                metadata={"department": "Leadership/Admin"},
            ),
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.METRIC,
                source="calendar-audit",
                content=(
                    f"A calendar audit shows leadership collectively spends about {hours} "
                    "hours per month reviewing the existing operations reports."
                ),
                metadata={"hours_per_month": hours},
            ),
        ],
        arithmetic=(
            f"{DASHBOARD}: DECOY — {hours} hr/mo x 12 x ${rate}/hr = ${truth:,.0f}/yr "
            "even if fully eliminated"
        ),
    )


def _discount_policy_evidence(rng: Random, *, emphasized: bool) -> list[Evidence]:
    items = [
        Evidence(
            id=_uuid(rng), kind=EvidenceKind.DOCUMENT,
            source="discount-policy",
            content=(
                "Discounts at or below 5% may be approved by the account owner. "
                "Discounts above 5% and at or below 12% require a sales manager. "
                "Discounts above 12% require VP Sales approval. Customer-facing "
                "quotes must not be sent before the required approval is recorded."
            ),
            metadata={"department": "Sales", "policy": True},
        )
    ]
    if emphasized:
        items.append(
            Evidence(
                id=_uuid(rng), kind=EvidenceKind.DOCUMENT,
                source="compliance-memo",
                content=(
                    "A compliance memo, issued after a mis-sent quote last year, "
                    "reiterates that no system or person may send a customer-facing "
                    "quote without a recorded approval; violations are escalated to "
                    "the audit committee."
                ),
                metadata={"policy": True},
            )
        )
    return items


def _targets(rng: Random, archetype: str) -> dict[str, float | None]:
    """Draw intended annual-value targets per area. None = unsizeable this case."""
    policy_sized = rng.random() < 0.5
    policy: float | None = rng.uniform(3_000, 10_000) if policy_sized else None
    if archetype == "quote_dominant":
        return {QUOTE: rng.uniform(34_000, 56_000), SUPPORT: rng.uniform(6_000, 18_000),
                FINANCE: rng.uniform(4_000, 12_000), POLICY: policy}
    if archetype == "triage_dominant":
        return {QUOTE: rng.uniform(8_000, 22_000), SUPPORT: rng.uniform(42_000, 88_000),
                FINANCE: rng.uniform(4_000, 12_000), POLICY: policy}
    if archetype == "finance_dominant":
        return {QUOTE: rng.uniform(4_000, 11_000), SUPPORT: rng.uniform(4_000, 11_000),
                FINANCE: rng.uniform(15_000, 20_500), POLICY: None}
    if archetype == "near_tie":
        top = rng.uniform(30_000, 52_000)
        second = top * rng.uniform(0.88, 0.97)
        pair = [top, second]
        rng.shuffle(pair)
        return {QUOTE: pair[0], SUPPORT: pair[1],
                FINANCE: rng.uniform(4_000, 12_000), POLICY: policy}
    if archetype == "decoy_prominent":
        winner_is_quote = rng.random() < 0.5
        big, small = rng.uniform(30_000, 55_000), rng.uniform(6_000, 16_000)
        return {QUOTE: big if winner_is_quote else small,
                SUPPORT: small if winner_is_quote else big,
                FINANCE: rng.uniform(4_000, 12_000), POLICY: policy}
    if archetype == "insufficient_policy":
        winner_is_quote = rng.random() < 0.5
        big, small = rng.uniform(28_000, 50_000), rng.uniform(8_000, 18_000)
        return {QUOTE: big if winner_is_quote else small,
                SUPPORT: small if winner_is_quote else big,
                FINANCE: rng.uniform(4_000, 12_000), POLICY: None}
    if archetype == "policy_trap":
        return {QUOTE: rng.uniform(34_000, 56_000), SUPPORT: rng.uniform(6_000, 16_000),
                FINANCE: rng.uniform(4_000, 12_000), POLICY: policy}
    if archetype == "contradictory_support":
        return {QUOTE: rng.uniform(26_000, 45_000), SUPPORT: rng.uniform(15_000, 35_000),
                FINANCE: rng.uniform(8_000, 14_000), POLICY: None}
    raise ValueError(f"unknown archetype: {archetype}")


def _intended_winner(archetype: str, targets: dict[str, float | None]) -> str:
    sized = {key: value for key, value in targets.items() if value is not None}
    if archetype == "contradictory_support":
        sized.pop(SUPPORT, None)
    return max(sized, key=lambda key: sized[key] or 0.0)


def _generate_case(
    rng: Random, params: GeneratorParams, archetype: str, index: int, company: dict[str, Any]
) -> tuple[BenchmarkCase, CaseAnswerKey, CaseManifest]:
    contradictory = archetype == "contradictory_support"
    for _ in range(25):
        targets = _targets(rng, archetype)
        winner = _intended_winner(archetype, targets)
        areas = [
            _quote_area(rng, params, targets[QUOTE] or 0.0),
            _support_area(rng, params, targets[SUPPORT] or 0.0, contradictory=contradictory),
            _finance_area(rng, params, targets[FINANCE] or 0.0),
            _policy_area(
                rng, params, targets[POLICY],
                high_volume=archetype == "insufficient_policy",
            ),
            _procurement_area(rng, params),
        ]
        if archetype == "decoy_prominent":
            areas.append(_decoy_area(rng, params))
        truths = {area.category: area.truth_usd for area in areas}
        sized = {key: value for key, value in truths.items() if value is not None}
        others = [value for key, value in sized.items() if key != winner]
        top_truth = sized.get(winner)
        if top_truth is None:
            continue
        if archetype == "near_tie":
            second = max(others) if others else 0.0
            if second >= top_truth or second / top_truth < 0.82:
                continue
        elif others and max(others) > top_truth / 1.08:
            continue  # clamping eroded the intended margin; redraw
        break
    else:
        raise RuntimeError(f"could not satisfy archetype {archetype} after 25 draws")

    evidence = [item for area in areas for item in area.evidence]
    evidence.extend(_discount_policy_evidence(rng, emphasized=archetype == "policy_trap"))

    banded = sorted(sized, key=lambda key: -sized[key])
    unsized = sorted(
        (area for area in areas if area.truth_usd is None),
        key=lambda area: -area.conservative_usd,
    )
    ranking = banded + [area.category for area in unsized]
    high_value = [
        key for key in banded
        if sized[key] >= params.high_value_floor_usd and key != DASHBOARD
    ] or [banded[0]]
    width = params.band_width
    bands = {
        key: ValueBand(low_usd=value * (1 - width), high_usd=value * (1 + width))
        for key, value in sized.items()
    }

    needs_policy_language = archetype in {"policy_trap", "quote_dominant"} or winner == QUOTE
    answer = CaseAnswerKey(
        case_id=f"ns-{index:03d}",
        true_ranking=ranking,
        high_value_categories=high_value,
        decoy_categories=[DASHBOARD] if archetype == "decoy_prominent" else [],
        insufficient_evidence_categories=[area.category for area in unsized],
        value_bands=bands,
        required_policy_keywords=["approval"] if needs_policy_language else [],
        prohibited_action_keywords=(
            list(PROHIBITED_QUOTE_ACTIONS) if archetype == "policy_trap" else []
        ),
        notes=f"[{archetype}] " + " | ".join(area.arithmetic for area in areas),
    )
    case = BenchmarkCase(
        case_id=f"ns-{index:03d}",
        variant_id=f"v{index:03d}",  # deliberately opaque: archetype lives in the answer only
        company=company,
        evidence=evidence,
    )
    manifest = CaseManifest(
        case_id=case.case_id,
        archetype=archetype,
        truth_usd=truths,
        arithmetic=[area.arithmetic for area in areas],
    )
    return case, answer, manifest


def generate_pack(
    params: GeneratorParams, company: dict[str, Any]
) -> tuple[BenchmarkPack, PackManifest]:
    rng = Random(params.require_seed())
    cases: list[BenchmarkCase] = []
    answers: list[CaseAnswerKey] = []
    manifests: list[CaseManifest] = []
    for index in range(1, params.case_count + 1):
        archetype = ARCHETYPES[(index - 1) % len(ARCHETYPES)]
        case, answer, manifest = _generate_case(rng, params, archetype, index, company)
        cases.append(case)
        answers.append(answer)
        manifests.append(manifest)
    pack = BenchmarkPack(
        pack_version=params.pack_version,
        category_rules=CATEGORY_RULES,
        cases=cases,
        answers=answers,
    )
    return pack, PackManifest(params=params, pack_hash=pack.pack_hash, cases=manifests)


def load_params(text: str) -> GeneratorParams:
    return GeneratorParams.model_validate(json.loads(text))
