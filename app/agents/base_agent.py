"""
Base Agent - LangGraph-based AI agents with tool calling
Uses LangGraph's create_react_agent pattern for proper agent behavior
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Sequence
from pydantic import BaseModel
from langchain_core.tools import tool, BaseTool, StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, END
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger

logger = get_logger("agent")


class AgentResult(BaseModel):
    """Standard result structure for agent operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str = ""


class LangGraphAgent(ABC):
    """
    Abstract base class for LangGraph-based agents.
    
    Uses LangGraph's ReAct pattern with tool-calling for:
    - Autonomous decision making
    - Tool execution
    - Multi-step reasoning
    """
    
    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.settings = get_settings()
        self.logger = get_logger(f"agent.{name}")
        self._tools: List[BaseTool] = []
        self._system_prompt = system_prompt or self._default_system_prompt()
        self._agent = None
        
        # Initialize LLM
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.fast_model,
            temperature=0.1,
        )
        
        self.smart_llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.smart_model,
            temperature=0.7,
        )
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent"""
        return f"""You are an AI assistant specialized in {self.name} tasks.
You have access to tools to help accomplish your goals.
Always use the appropriate tool when needed.
Think step by step and explain your reasoning."""
    
    def add_tool(self, func: Callable, name: str = None, description: str = None) -> BaseTool:
        """
        Add a tool to this agent.
        
        Args:
            func: The function to wrap as a tool
            name: Tool name (defaults to function name)
            description: Tool description
            
        Returns:
            The wrapped tool
        """
        wrapped_tool = StructuredTool.from_function(
            func=func,
            name=name or func.__name__,
            description=description or func.__doc__ or "No description",
        )
        self._tools.append(wrapped_tool)
        self.logger.debug(f"Added tool: {wrapped_tool.name}")
        return wrapped_tool
    
    def get_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return self._tools
    
    def _build_agent(self, use_smart: bool = False):
        """Build the LangGraph ReAct agent"""
        llm = self.smart_llm if use_smart else self.llm
        
        # Create ReAct agent with tools
        agent = create_react_agent(
            model=llm,
            tools=self._tools,
            state_modifier=self._system_prompt,
        )
        
        return agent
    
    async def invoke(
        self,
        query: str,
        use_smart: bool = False,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        Invoke the agent with a query.
        
        Args:
            query: The user query/task
            use_smart: Use the larger model
            max_iterations: Maximum reasoning steps
            
        Returns:
            Agent response with messages and tool outputs
        """
        agent = self._build_agent(use_smart)
        
        # Prepare input
        input_messages = {"messages": [HumanMessage(content=query)]}
        
        try:
            # Run agent
            result = await agent.ainvoke(
                input_messages,
                config={"recursion_limit": max_iterations * 2}
            )
            
            # Extract final response
            messages = result.get("messages", [])
            final_message = messages[-1] if messages else None
            
            return {
                "success": True,
                "response": final_message.content if final_message else "",
                "messages": messages,
                "tool_calls": self._extract_tool_calls(messages),
            }
            
        except Exception as e:
            self.logger.error(f"Agent invocation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "",
            }
    
    def _extract_tool_calls(self, messages: List) -> List[Dict]:
        """Extract tool calls from message history"""
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    })
        return tool_calls
    
    @abstractmethod
    async def run(self, **kwargs) -> AgentResult:
        """
        Main execution method for the agent.
        Must be implemented by subclasses.
        """
        pass
    
    def _success(self, data: Any = None, message: str = "") -> AgentResult:
        """Create success result"""
        return AgentResult(
            success=True,
            data=data if isinstance(data, dict) else {"result": data},
            message=message,
        )
    
    def _error(self, error: str, data: Any = None) -> AgentResult:
        """Create error result"""
        self.logger.error(f"Agent error: {error}")
        return AgentResult(
            success=False,
            error=error,
            data=data if isinstance(data, dict) else None,
        )


class SimpleAgent(ABC):
    """
    Simple agent without full ReAct pattern.
    For straightforward tasks that don't need multi-step reasoning.
    Uses LangChain's tool-calling directly.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.settings = get_settings()
        self.logger = get_logger(f"agent.{name}")
        
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.fast_model,
            temperature=0.1,
        )
        
        self.smart_llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.smart_model,
            temperature=0.7,
        )
    
    async def invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        use_smart: bool = False,
    ) -> str:
        """Invoke LLM with prompts"""
        llm = self.smart_llm if use_smart else self.llm
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        self.logger.debug(f"Invoking LLM (smart={use_smart})")
        response = await llm.ainvoke(messages)
        
        return response.content
    
    async def invoke_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        use_smart: bool = False,
    ) -> Dict[str, Any]:
        """Invoke LLM and parse JSON response"""
        import json
        
        response = await self.invoke_llm(system_prompt, user_prompt, use_smart)
        
        # Extract JSON from response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")
    
    @abstractmethod
    async def run(self, **kwargs) -> AgentResult:
        """Main execution method"""
        pass
    
    def _success(self, data: Any = None, message: str = "") -> AgentResult:
        """Create success result"""
        return AgentResult(
            success=True,
            data=data if isinstance(data, dict) else {"result": data},
            message=message,
        )
    
    def _error(self, error: str, data: Any = None) -> AgentResult:
        """Create error result"""
        self.logger.error(f"Agent error: {error}")
        return AgentResult(
            success=False,
            error=error,
            data=data if isinstance(data, dict) else None,
        )


# Backwards compatibility - alias for existing agents
BaseAgent = SimpleAgent
