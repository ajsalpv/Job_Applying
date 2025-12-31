"""
Agents package initialization
"""
from app.agents.base_agent import (
    LangGraphAgent,
    SimpleAgent,
    BaseAgent,  # Alias for backwards compat
    AgentResult,
)

__all__ = [
    "LangGraphAgent",
    "SimpleAgent",
    "BaseAgent",
    "AgentResult",
]
