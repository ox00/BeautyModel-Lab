import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.loaders.csv_loader import BatchLoader
from src.pipeline import OpenAICompatibleToolAgent, TemporaryRAGAgent
from src.retrieval import build_indexes


DEMO_REQUESTS = [
    ("PHERETIMA GUILLELMI EXTRACT 有什么功效", None),
    ("冰晶眼膜 最近有什么趋势", {"need_trend": True}),
    ("乳黄素 是否合规", None),
    ("不存在的奇怪查询 123456", None),
]


def _print_result(query: str, result: dict) -> None:
    import json

    print(f"\n--- agent query={query} ---")
    print(result["final_answer"])
    print("tool_payload:")
    print(json.dumps(result["tool_payload"], ensure_ascii=False, indent=2, sort_keys=True))


def _run_preset_demo(llm_agent: OpenAICompatibleToolAgent) -> None:
    for query, filters in DEMO_REQUESTS:
        user_query = query if not filters else f"{query}\nfilters={filters}"
        result = llm_agent.run(user_query)
        _print_result(query, result)


def _run_interactive_demo(llm_agent: OpenAICompatibleToolAgent) -> None:
    print("输入你的问题开始验证，输入 `exit` / `quit` 结束。")
    print("如果想附带 filters，可以直接输入 JSON，例如：{\"query\": \"冰晶眼膜 最近有什么趋势\", \"filters\": {\"need_trend\": true}}")

    while True:
        try:
            raw_input_value = input("\nuser> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已退出。")
            break

        if not raw_input_value:
            continue
        if raw_input_value.lower() in {"exit", "quit", "q"}:
            print("已退出。")
            break

        query = raw_input_value
        filters = None
        if raw_input_value.startswith("{") and raw_input_value.endswith("}"):
            try:
                import json

                payload = json.loads(raw_input_value)
                query = payload.get("query", "").strip()
                filters = payload.get("filters")
            except Exception:
                print("JSON 解析失败，请直接输入问题，或使用标准 JSON 格式。")
                continue

        if not query:
            print("问题不能为空。")
            continue

        user_query = query if not filters else f"{query}\nfilters={filters}"
        result = llm_agent.run(user_query)
        _print_result(query, result)


def main():
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    batch_bundle = BatchLoader.load_batch(data_path, include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(batch_bundle)
    rag_agent = TemporaryRAGAgent(retrieval_bundle)
    llm_agent = OpenAICompatibleToolAgent.from_project_env(rag_agent, project_root)

    print("=== LLM Tool Agent Demo ===")
    print(f"batch_version: {retrieval_bundle.batch_version}")

    if sys.stdin.isatty():
        _run_interactive_demo(llm_agent)
    else:
        _run_preset_demo(llm_agent)


if __name__ == "__main__":
    main()
