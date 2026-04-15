"""QA core package for first-party trend_signal retrieval integration and gating hardening (QA-002)."""

from .models import TrendSignal, TrendEvidence, QAResult
from .trend_retrieval import TrendSignalRepository, TrendRetrievalConfig
from .pipeline import QAPipeline

__all__ = [
    "TrendSignal",
    "TrendEvidence",
    "QAResult",
    "TrendSignalRepository",
    "TrendRetrievalConfig",
    "QAPipeline",
]
