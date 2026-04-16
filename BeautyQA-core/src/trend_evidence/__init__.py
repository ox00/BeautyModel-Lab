"""Trend evidence ingestion and retrieval package for first-party trend_signal handoff."""

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
