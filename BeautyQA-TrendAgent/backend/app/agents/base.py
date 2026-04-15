from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentContext:
    """Shared context passed between agents in a pipeline."""

    task_id: int = 0
    keyword_id: int = 0
    keyword: str = ""
    platform: str = ""
    account_id: Optional[int] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result returned by an agent execution."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class BaseAgent(ABC):
    """Base class for all agents in the Multi-Agent system."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and identification."""
        ...

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's logic.

        Args:
            context: Shared context from previous agents or caller.

        Returns:
            AgentResult with success status and output data.
        """
        ...
