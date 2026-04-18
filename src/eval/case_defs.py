from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RetrievalEvalCase:
    case_id: str
    query: str
    intent: str
    expected_tables: List[str]
    description: Optional[str] = None
    filters: Optional[Dict[str, str]] = None
    requires_risk_flag: bool = False


@dataclass
class RetrievalEvalCaseResult:
    case: RetrievalEvalCase
    returned_tables: List[str]
    hit: bool
    risk_flag_hit: bool
    missing_info_note: Optional[str] = None


@dataclass
class RetrievalEvalReport:
    results: List[RetrievalEvalCaseResult]
    metrics: Dict[str, float]
    release_checklist: Dict[str, bool] = field(default_factory=dict)


@dataclass
class AnswerEvalCase:
    case_id: str
    query: str
    expected_intent: str
    requires_scientific_basis: bool = False
    requires_trend_basis: bool = False
    requires_safety_warning: bool = False
    expects_missing_info: bool = False
    requires_trace_coverage: bool = True
    filters: Optional[Dict[str, str]] = None


@dataclass
class AnswerEvalCaseResult:
    case: AnswerEvalCase
    answer: "AnswerResult"
    scientificity_pass: bool
    trend_relevance_pass: bool
    safety_pass: bool
    balance_pass: bool
    missing_info_behavior_pass: bool
    trace_coverage_pass: bool


@dataclass
class AnswerEvalReport:
    results: List[AnswerEvalCaseResult]
    metrics: Dict[str, float]
    release_checklist: Dict[str, bool] = field(default_factory=dict)
