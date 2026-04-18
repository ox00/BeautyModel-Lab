from pathlib import Path

from src.eval import evaluate_answer_bundle, get_default_answer_eval_cases
from src.loaders.csv_loader import BatchLoader
from src.pipeline import (
    OpenAICompatibleToolAgent,
    TemporaryRAGAgent,
    answer_query,
    classify_intent,
    load_project_env,
)
from src.retrieval import build_indexes, search_all


P0_DATA_PATH = Path("data/deliveries/2026-03-14-baseline-v1/p0").resolve()


def _build_retrieval_bundle():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH), include_optional_tables=["review_feedback_raw"])
    return build_indexes(bundle)


def test_classify_intent_routes_core_queries():
    assert classify_intent("PHERETIMA GUILLELMI EXTRACT 有什么功效") == "science"
    assert classify_intent("冰晶眼膜 最近有什么趋势", {"need_trend": True}) == "trend"
    assert classify_intent("乳黄素 是否合规") == "compliance"


def test_search_all_hybrid_handles_weak_expression():
    retrieval_bundle = _build_retrieval_bundle()

    items = search_all(retrieval_bundle, query="眼部冰凉贴片", intent="trend", mode="hybrid")

    assert items
    assert any(item.source_table == "trend_signal" for item in items)


def test_answer_query_science_contains_scientific_basis_and_trace():
    retrieval_bundle = _build_retrieval_bundle()

    answer = answer_query(retrieval_bundle, "PHERETIMA GUILLELMI EXTRACT 有什么功效")

    assert answer.scientific_basis
    assert answer.cited_trace_ids
    assert "Scientific basis:" in answer.answer_text


def test_answer_query_trend_contains_trend_basis():
    retrieval_bundle = _build_retrieval_bundle()

    answer = answer_query(retrieval_bundle, "冰晶眼膜 最近有什么趋势", filters={"need_trend": True})

    assert answer.trend_basis
    assert "Trend basis:" in answer.answer_text


def test_answer_query_compliance_contains_safety_warning():
    retrieval_bundle = _build_retrieval_bundle()

    answer = answer_query(retrieval_bundle, "乳黄素 是否合规")

    assert answer.safety_warning or answer.risk_note
    assert answer.cited_trace_ids


def test_answer_query_missing_info_degrades_safely():
    retrieval_bundle = _build_retrieval_bundle()

    answer = answer_query(retrieval_bundle, "不存在的奇怪查询 123456")

    assert answer.missing_info_note is not None
    assert answer.recommendation.startswith("暂不做强推荐")
    assert answer.cited_trace_ids == []


def test_answer_eval_bundle_reports_gate_metrics():
    retrieval_bundle = _build_retrieval_bundle()

    report = evaluate_answer_bundle(retrieval_bundle, get_default_answer_eval_cases())

    assert report.metrics["scientificity"] >= 0.8
    assert report.metrics["safety"] >= 1.0
    assert report.metrics["trace_coverage"] >= 0.8
    assert report.release_checklist["safety_ready"] is True


def test_temporary_agent_adapter_exposes_tool_payload():
    retrieval_bundle = _build_retrieval_bundle()
    agent = TemporaryRAGAgent(retrieval_bundle)

    result = agent.run("乳黄素 是否合规")

    assert result.intent == "compliance"
    assert result.cited_trace_ids
    assert "answer_text" in result.tool_payload
    assert result.tool_payload["intent"] == "compliance"


def test_load_project_env_reads_key_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=test-key\nOPENAI_MODEL=test-model\n", encoding="utf-8")

    env = load_project_env(str(tmp_path))

    assert env["OPENAI_API_KEY"] == "test-key"
    assert env["OPENAI_MODEL"] == "test-model"


def test_openai_compatible_tool_agent_tool_loop():
    retrieval_bundle = _build_retrieval_bundle()
    rag_agent = TemporaryRAGAgent(retrieval_bundle)
    agent = OpenAICompatibleToolAgent(
        rag_agent,
        config=type("Cfg", (), {"api_key": "x", "model": "m", "base_url": "http://example.com", "system_prompt": "s"})(),
    )

    responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "grounded_rag_lookup",
                                    "arguments": '{"query":"乳黄素 是否合规"}',
                                },
                            }
                        ],
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "content": "基于检索结果，乳黄素相关回答需要保留合规提示。"
                    }
                }
            ]
        },
    ]

    def fake_chat_completion(messages, tools):
        return responses.pop(0)

    agent._chat_completion = fake_chat_completion  # type: ignore[method-assign]

    result = agent.run("乳黄素 是否合规")

    assert "基于检索结果" in result["final_answer"]
    assert result["tool_payload"] is not None
    assert result["tool_payload"]["intent"] == "compliance"
