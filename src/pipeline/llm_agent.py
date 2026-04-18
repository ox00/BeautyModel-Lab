from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, request

from src.pipeline.agent_adapter import TemporaryRAGAgent


@dataclass
class LLMToolAgentConfig:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    system_prompt: str = (
        "You are a beauty QA agent. Use the available tool when you need grounded evidence. "
        "You must preserve risk notes and missing-info notes from tool outputs."
    )


class OpenAICompatibleToolAgent:
    """Minimal OpenAI-compatible tool-calling wrapper for the current RAG system."""

    def __init__(self, rag_agent: TemporaryRAGAgent, config: LLMToolAgentConfig):
        self.rag_agent = rag_agent
        self.config = config

    @classmethod
    def from_project_env(cls, rag_agent: TemporaryRAGAgent, project_root: str) -> "OpenAICompatibleToolAgent":
        env = load_project_env(project_root)
        api_key = env.get("OPENAI_API_KEY")
        model = env.get("OPENAI_MODEL") or env.get("MODEL")
        base_url = env.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        if not api_key or not model:
            raise ValueError(
                "Missing OPENAI_API_KEY or OPENAI_MODEL in project root .env. "
                "Please add them before running the live agent demo."
            )
        return cls(
            rag_agent=rag_agent,
            config=LLMToolAgentConfig(api_key=api_key, model=model, base_url=base_url),
        )

    def run(self, user_query: str) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": user_query},
        ]
        tools = [self._tool_spec()]
        first_response = self._chat_completion(messages=messages, tools=tools)
        assistant_message = first_response["choices"][0]["message"]

        tool_calls = assistant_message.get("tool_calls") or []
        if not tool_calls:
            return {
                "final_answer": assistant_message.get("content", ""),
                "raw_response": first_response,
                "tool_payload": None,
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.get("content"),
                "tool_calls": tool_calls,
            }
        )

        last_tool_payload = None
        for tool_call in tool_calls:
            if tool_call["function"]["name"] != "grounded_rag_lookup":
                continue
            arguments = json.loads(tool_call["function"]["arguments"])
            query = arguments["query"]
            filters = arguments.get("filters")
            tool_payload = self.rag_agent.tool_call(query=query, filters=filters)
            last_tool_payload = tool_payload
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": "grounded_rag_lookup",
                    "content": json.dumps(tool_payload, ensure_ascii=False),
                }
            )

        second_response = self._chat_completion(messages=messages, tools=tools)
        final_message = second_response["choices"][0]["message"]
        return {
            "final_answer": final_message.get("content", ""),
            "raw_response": second_response,
            "tool_payload": last_tool_payload,
        }

    def _chat_completion(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM API request failed: {exc.code} {detail}") from exc

    @staticmethod
    def _tool_spec() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "grounded_rag_lookup",
                "description": "Query the grounded RAG system and return evidence-backed answer components.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "filters": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "product_id": {"type": "string"},
                                "need_trend": {"type": "boolean"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }


def load_project_env(project_root: str) -> Dict[str, str]:
    env_path = Path(project_root) / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"Project root .env not found: {env_path}")

    env: Dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("\"").strip("'")
    for key, value in os.environ.items():
        env.setdefault(key, value)
    return env
