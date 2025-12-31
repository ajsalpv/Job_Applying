"""
Groq LLM Client - LangChain wrapper for Groq API
"""
import json
from typing import Optional, Dict, Any, Type
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger
from app.tools.utils.retry import llm_retry

logger = get_logger("llm")


class GroqClient:
    """LangChain-based Groq LLM client with model selection"""
    
    def __init__(self):
        self.settings = get_settings()
        self._fast_model: Optional[ChatGroq] = None
        self._smart_model: Optional[ChatGroq] = None
    
    @property
    def fast_model(self) -> ChatGroq:
        """Get fast model for quick tasks (scoring, extraction)"""
        if self._fast_model is None:
            self._fast_model = ChatGroq(
                api_key=self.settings.groq_api_key,
                model_name=self.settings.fast_model,
                temperature=0.1,
                max_tokens=2048,
            )
        return self._fast_model
    
    @property
    def smart_model(self) -> ChatGroq:
        """Get smart model for complex tasks (writing, analysis)"""
        if self._smart_model is None:
            self._smart_model = ChatGroq(
                api_key=self.settings.groq_api_key,
                model_name=self.settings.smart_model,
                temperature=0.7,
                max_tokens=4096,
            )
        return self._smart_model
    
    def get_model(self, use_smart: bool = False) -> ChatGroq:
        """Get appropriate model based on task complexity"""
        return self.smart_model if use_smart else self.fast_model
    
    @llm_retry
    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        use_smart: bool = False,
    ) -> str:
        """
        Invoke LLM with system and user prompts.
        
        Args:
            system_prompt: System context/instructions
            user_prompt: User query/task
            use_smart: Use larger model for complex tasks
            
        Returns:
            LLM response as string
        """
        model = self.get_model(use_smart)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        logger.debug(f"Invoking LLM ({model.model_name})")
        response = await model.ainvoke(messages)
        
        return response.content
    
    @llm_retry
    async def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        use_smart: bool = False,
    ) -> Dict[str, Any]:
        """
        Invoke LLM and parse response as JSON.
        
        Args:
            system_prompt: System context/instructions
            user_prompt: User query/task
            schema: Optional Pydantic model for response validation
            use_smart: Use larger model for complex tasks
            
        Returns:
            Parsed JSON response as dictionary
        """
        response = await self.invoke(system_prompt, user_prompt, use_smart)
        
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            parsed = json.loads(json_str.strip())
            
            # Validate against schema if provided
            if schema:
                validated = schema.model_validate(parsed)
                return validated.model_dump()
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")


# Singleton instance
groq_client = GroqClient()
