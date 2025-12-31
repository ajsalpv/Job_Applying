"""
Prompt Executor - Execute prompts with variable substitution
"""
from typing import Dict, Any
from app.tools.llm.groq_client import groq_client
from app.config.settings import get_settings
from app.config.constants import USER_SKILLS
from app.tools.utils.logger import get_logger

logger = get_logger("prompt_executor")


class PromptExecutor:
    """Execute prompts with automatic variable substitution"""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = groq_client
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Get default context variables from settings"""
        return {
            "user_name": self.settings.user_name,
            "user_email": self.settings.user_email,
            "user_phone": self.settings.user_phone,
            "location": self.settings.user_location,
            "experience_years": self.settings.experience_years,
            "skills": ", ".join(USER_SKILLS[:15]),  # Top 15 skills
            "target_roles": self.settings.target_roles,
        }
    
    def _substitute_variables(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """Substitute variables in template with context values"""
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context variable: {e}")
            return template
    
    async def execute(
        self,
        system_template: str,
        user_template: str,
        context: Dict[str, Any] = None,
        use_smart: bool = False,
    ) -> str:
        """
        Execute a prompt with variable substitution.
        
        Args:
            system_template: System prompt template
            user_template: User prompt template
            context: Additional context variables
            use_smart: Use larger model
            
        Returns:
            LLM response
        """
        # Merge default context with provided context
        full_context = self._get_default_context()
        if context:
            full_context.update(context)
        
        # Substitute variables
        system_prompt = self._substitute_variables(system_template, full_context)
        user_prompt = self._substitute_variables(user_template, full_context)
        
        logger.debug(f"Executing prompt (smart={use_smart})")
        
        return await self.llm.invoke(system_prompt, user_prompt, use_smart)
    
    async def execute_json(
        self,
        system_template: str,
        user_template: str,
        context: Dict[str, Any] = None,
        use_smart: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a prompt and parse response as JSON.
        
        Args:
            system_template: System prompt template
            user_template: User prompt template
            context: Additional context variables
            use_smart: Use larger model
            
        Returns:
            Parsed JSON response
        """
        full_context = self._get_default_context()
        if context:
            full_context.update(context)
        
        system_prompt = self._substitute_variables(system_template, full_context)
        user_prompt = self._substitute_variables(user_template, full_context)
        
        return await self.llm.invoke_json(system_prompt, user_prompt, use_smart=use_smart)


# Singleton instance
prompt_executor = PromptExecutor()
