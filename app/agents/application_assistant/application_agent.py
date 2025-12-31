"""
Application Assistant Agent - Human-in-the-loop application workflow
"""
from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent, AgentResult
from app.tools.browser import playwright_manager
from app.config.prompts import FORM_FILLING_SYSTEM, FORM_FILLING_USER
from app.config.constants import ApplicationStatus


class ApplicationAgent(BaseAgent):
    """
    Agent for assisting with job applications.
    
    IMPORTANT: This agent is designed for human-in-the-loop operation.
    It will NEVER auto-submit applications.
    
    Features:
    - Opens job application page
    - Extracts form fields
    - Suggests answers to questions
    - Waits for human approval before any action
    """
    
    def __init__(self):
        super().__init__("application")
    
    async def extract_form_fields(self, page) -> List[Dict[str, Any]]:
        """
        Extract form fields from application page.
        
        Returns:
            List of form field dictionaries
        """
        fields = []
        
        try:
            # Common form selectors
            inputs = await page.query_selector_all("input, textarea, select")
            
            for input_el in inputs:
                try:
                    input_type = await input_el.get_attribute("type") or "text"
                    name = await input_el.get_attribute("name") or ""
                    label_text = ""
                    
                    # Try to find associated label
                    input_id = await input_el.get_attribute("id")
                    if input_id:
                        label = await page.query_selector(f'label[for="{input_id}"]')
                        if label:
                            label_text = await label.text_content() or ""
                    
                    # Skip hidden fields
                    if input_type == "hidden":
                        continue
                    
                    fields.append({
                        "type": input_type,
                        "name": name,
                        "label": label_text.strip(),
                        "required": await input_el.get_attribute("required") is not None,
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to extract form fields: {e}")
        
        return fields
    
    async def suggest_answer(
        self,
        question: str,
        field_type: str = "text",
    ) -> Dict[str, Any]:
        """
        Generate suggested answer for a form question.
        
        Args:
            question: The form question/label
            field_type: Type of input field
            
        Returns:
            Suggested answer with confidence
        """
        context = {
            "question": question,
        }
        
        try:
            result = await self.execute_prompt_json(
                FORM_FILLING_SYSTEM,
                FORM_FILLING_USER,
                context,
                use_smart=False,  # Use fast model
            )
            
            return {
                "answer": result.get("answer", ""),
                "confidence": result.get("confidence", "low"),
                "needs_review": result.get("needs_review", True),
                "notes": result.get("notes", ""),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to suggest answer: {e}")
            return {
                "answer": "",
                "confidence": "low",
                "needs_review": True,
                "notes": f"Error: {str(e)}",
            }
    
    async def prepare_application(
        self,
        job_url: str,
    ) -> Dict[str, Any]:
        """
        Prepare application by analyzing the job page.
        
        This opens the page, extracts information, but DOES NOT submit anything.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Application preparation data
        """
        self.logger.info(f"Preparing application for: {job_url}")
        
        preparation = {
            "job_url": job_url,
            "form_fields": [],
            "suggested_answers": [],
            "status": "prepared",
            "requires_human_review": True,
        }
        
        try:
            async with playwright_manager.get_page() as page:
                await playwright_manager.navigate(page, job_url)
                
                # Extract form fields
                fields = await self.extract_form_fields(page)
                preparation["form_fields"] = fields
                
                # Generate suggestions for text fields
                for field in fields:
                    if field.get("label") and field.get("type") in ["text", "textarea"]:
                        suggestion = await self.suggest_answer(
                            field["label"],
                            field["type"],
                        )
                        preparation["suggested_answers"].append({
                            "field": field["name"] or field["label"],
                            **suggestion,
                        })
                
                # Take screenshot for reference
                await page.screenshot(path=f"logs/application_{hash(job_url)}.png")
                
        except Exception as e:
            self.logger.error(f"Preparation failed: {e}")
            preparation["status"] = "error"
            preparation["error"] = str(e)
        
        return preparation
    
    async def run(
        self,
        jobs: List[Dict[str, Any]],
    ) -> AgentResult:
        """
        Prepare applications for review (NO auto-submission).
        
        Args:
            jobs: List of job dictionaries to prepare applications for
            
        Returns:
            AgentResult with prepared applications awaiting review
        """
        self.logger.info(f"Preparing {len(jobs)} applications for review")
        
        preparations = []
        
        for job in jobs:
            try:
                prep = await self.prepare_application(job.get("job_url", ""))
                preparations.append({
                    "company": job.get("company"),
                    "role": job.get("role"),
                    **prep,
                })
            except Exception as e:
                self.logger.error(f"Error preparing {job.get('company')}: {e}")
                continue
        
        return self._success(
            data={
                "preparations": preparations,
                "message": "⚠️ HUMAN REVIEW REQUIRED - Applications prepared but NOT submitted",
            },
            message=f"Prepared {len(preparations)} applications for human review"
        )


application_agent = ApplicationAgent()
