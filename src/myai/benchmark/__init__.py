"""Public benchmark framework.

Schemas, deterministic scoring, pack loading, and report aggregation. Real
answer keys are loaded from a private pack and must never be committed here.
"""

from myai.benchmark.categories import match_category, predicted_category_order
from myai.benchmark.loader import (
    PACK_ENV_VAR,
    BenchmarkPackLoader,
    FilesystemPackLoader,
    default_pack_path,
    load_default_pack,
)
from myai.benchmark.report import BenchmarkReport, CaseRun, build_report, top1_stability
from myai.benchmark.schema import (
    BenchmarkCase,
    BenchmarkPack,
    CaseAnswerKey,
    OpportunityCategoryRule,
    ValueBand,
)
from myai.benchmark.scoring import CaseScore, score_case, spearman

__all__ = [
    "PACK_ENV_VAR",
    "BenchmarkCase",
    "BenchmarkPack",
    "BenchmarkPackLoader",
    "BenchmarkReport",
    "CaseAnswerKey",
    "CaseRun",
    "CaseScore",
    "FilesystemPackLoader",
    "OpportunityCategoryRule",
    "ValueBand",
    "build_report",
    "default_pack_path",
    "load_default_pack",
    "match_category",
    "predicted_category_order",
    "score_case",
    "spearman",
    "top1_stability",
]
