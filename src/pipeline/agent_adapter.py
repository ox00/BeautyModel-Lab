from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.pipeline.core import AnswerResult, answer_query
from src.retrieval import RetrievalBundle


@dataclass
class AgentToolResult:
    final_answer: str
    intent: str
    cited_trace_ids: list[str]
    risk_note: Optional[str]
    missing_info_note: Optional[str]
    batch_version: Optional[str]
    tool_payload: Dict[str, Any]


class TemporaryRAGAgent:
    """Minimal agent-facing adapter for the current grounded RAG pipeline."""

    def __init__(self, retrieval_bundle: RetrievalBundle, mode: str = "auto"):
        self.retrieval_bundle = retrieval_bundle
        self.mode = mode

    def run(self, query: str, filters: Optional[Dict[str, Any]] = None) -> AgentToolResult:
        answer = answer_query(self.retrieval_bundle, query=query, filters=filters, mode=self.mode)
        return self._to_agent_result(answer)

    def tool_call(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        answer = answer_query(self.retrieval_bundle, query=query, filters=filters, mode=self.mode)
        return self._to_agent_result(answer).tool_payload

    @staticmethod
    def _to_agent_result(answer: AnswerResult) -> AgentToolResult:
        tool_payload = {
            "query": answer.query,
            "intent": answer.intent,
            "answer_text": answer.answer_text,
            "recommendation": answer.recommendation,
            "scientific_basis": answer.scientific_basis,
            "trend_basis": answer.trend_basis,
            "safety_warning": answer.safety_warning,
            "risk_note": answer.risk_note,
            "missing_info_note": answer.missing_info_note,
            "cited_trace_ids": answer.cited_trace_ids,
            "batch_version": answer.batch_version,
        }
        return AgentToolResult(
            final_answer=answer.answer_text,
            intent=answer.intent,
            cited_trace_ids=answer.cited_trace_ids,
            risk_note=answer.risk_note,
            missing_info_note=answer.missing_info_note,
            batch_version=answer.batch_version,
            tool_payload=tool_payload,
        )
