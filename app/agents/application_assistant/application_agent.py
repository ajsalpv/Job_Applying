"""
Application Assistant Agent - LangGraph-based human-in-the-loop application workflow
Uses LangGraph ReAct pattern with tools for form analysis and suggestion generation
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.tools.browser import playwright_manager
from app.config.prompts import FORM_FILLING_SYSTEM, FORM_FILLING_USER
from app.config.constants import ApplicationStatus, USER_SKILLS


# ============================================================
# APPLICATION ASSISTANT TOOLS
# ============================================================

@tool
def analyze_form_fields(fields_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze extracted form fields and categorize them.
    
    Args:
        fields_data: List of form field dictionaries with type, name, label, required
        
    Returns:
        Categorized fields with analysis
    """
    categories = {
        "personal_info": [],
        "experience": [],
        "skills": [],
        "cover_letter": [],
        "other": [],
    }
    
    for field in fields_data:
        label = field.get("label", "").lower()
        name = field.get("name", "").lower()
        field_type = field.get("type", "text")
        
        combined = f"{label} {name}"
        
        if any(kw in combined for kw in ["name", "email", "phone", "linkedin", "github"]):
            categories["personal_info"].append(field)
        elif any(kw in combined for kw in ["experience", "years", "work history"]):
            categories["experience"].append(field)
        elif any(kw in combined for kw in ["skill", "technology", "framework"]):
            categories["skills"].append(field)
        elif any(kw in combined for kw in ["cover", "letter", "motivation", "why"]):
            categories["cover_letter"].append(field)
        else:
            categories["other"].append(field)
    
    return {
        "categories": categories,
        "total_fields": len(fields_data),
        "required_fields": len([f for f in fields_data if f.get("required")]),
        "analysis": f"Found {len(fields_data)} fields: "
                    f"{len(categories['personal_info'])} personal, "
                    f"{len(categories['experience'])} experience, "
                    f"{len(categories['skills'])} skills, "
                    f"{len(categories['cover_letter'])} cover letter",
    }


@tool
def generate_answer_suggestion(
    question: str,
    field_type: str,
    job_role: str = "",
    company: str = "",
) -> Dict[str, Any]:
    """
    Generate a suggested answer for a form question based on user profile.
    
    Args:
        question: The form question/label text
        field_type: Type of input field (text, textarea, select)
        job_role: The role being applied for
        company: The company name
        
    Returns:
        Suggested answer with confidence level
    """
    question_lower = question.lower()
    
    # Standard answers based on question type
    standard_answers = {
        "name": {"answer": "Ajsal PV", "confidence": "high"},
        "email": {"answer": "pvajsal27@gmail.com", "confidence": "high"},
        "phone": {"answer": "+91 7356793165", "confidence": "high"},
        "linkedin": {"answer": "linkedin.com/in/ajsalpv", "confidence": "high"},
        "github": {"answer": "github.com/ajsalpv", "confidence": "high"},
        "experience": {"answer": "2 years", "confidence": "high"},
        "location": {"answer": "Kochi, Kerala, India (Open to relocation)", "confidence": "high"},
        "notice period": {"answer": "15 days", "confidence": "medium"},
        "current ctc": {"answer": "As per market standards", "confidence": "medium"},
        "expected ctc": {"answer": "Negotiable based on role", "confidence": "medium"},
    }
    
    # Check for standard questions
    for key, answer_data in standard_answers.items():
        if key in question_lower:
            return {
                **answer_data,
                "question": question,
                "needs_review": answer_data["confidence"] != "high",
            }
    
    # Skills-related questions
    if any(kw in question_lower for kw in ["skill", "technology", "expertise"]):
        relevant_skills = USER_SKILLS[:8]
        return {
            "answer": ", ".join(relevant_skills),
            "confidence": "high",
            "question": question,
            "needs_review": False,
        }
    
    # Cover letter / motivation
    if any(kw in question_lower for kw in ["why", "motivation", "cover", "interested"]):
        answer = f"""I am excited about the {job_role or 'AI/ML'} opportunity at {company or 'your company'} because of my strong background in AI development. With 2 years of experience building LLM-powered applications, RAG systems, and real-time AI solutions, I am confident I can contribute meaningfully to your team.

At Brevo Technologies, I developed multilingual voice AI agents with <500ms latency and automated interviewing systems using LangChain. I'm passionate about applying cutting-edge AI to solve real problems and would love to bring this expertise to {company or 'your team'}."""
        return {
            "answer": answer,
            "confidence": "medium",
            "question": question,
            "needs_review": True,
        }
    
    # Default - unclear question
    return {
        "answer": "",
        "confidence": "low",
        "question": question,
        "needs_review": True,
        "notes": "Unclear question - requires manual review",
    }


@tool
def validate_application_readiness(
    form_fields: List[Dict[str, Any]],
    suggested_answers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate if application is ready for human review.
    
    Args:
        form_fields: List of form fields
        suggested_answers: List of suggested answers
        
    Returns:
        Validation status and issues
    """
    issues = []
    warnings = []
    
    # Check required fields have answers
    required_fields = [f for f in form_fields if f.get("required")]
    answered_fields = [a for a in suggested_answers if a.get("answer")]
    
    if len(answered_fields) < len(required_fields):
        issues.append(f"Missing answers for {len(required_fields) - len(answered_fields)} required fields")
    
    # Check for low confidence answers
    low_confidence = [a for a in suggested_answers if a.get("confidence") == "low"]
    if low_confidence:
        warnings.append(f"{len(low_confidence)} answers need manual review (low confidence)")
    
    # Check for fields needing review
    needs_review = [a for a in suggested_answers if a.get("needs_review")]
    if needs_review:
        warnings.append(f"{len(needs_review)} answers flagged for review")
    
    is_ready = len(issues) == 0
    
    return {
        "is_ready": is_ready,
        "issues": issues,
        "warnings": warnings,
        "total_fields": len(form_fields),
        "answered": len(answered_fields),
        "needs_review": len(needs_review),
        "recommendation": "ready_for_review" if is_ready else "needs_attention",
    }


@tool
def generate_application_summary(
    company: str,
    role: str,
    form_fields_count: int,
    suggestions_count: int,
) -> Dict[str, Any]:
    """
    Generate a summary of the prepared application.
    
    Args:
        company: Company name
        role: Job role
        form_fields_count: Number of form fields found
        suggestions_count: Number of suggestions generated
        
    Returns:
        Application summary
    """
    return {
        "summary": f"Application prepared for {role} at {company}",
        "details": {
            "form_fields_found": form_fields_count,
            "suggestions_generated": suggestions_count,
            "status": "awaiting_human_review",
        },
        "next_steps": [
            "Review suggested answers for accuracy",
            "Complete any empty or low-confidence fields",
            "Submit application manually",
        ],
        "warning": "⚠️ HUMAN REVIEW REQUIRED - Application will NOT be auto-submitted",
    }


# ============================================================
# APPLICATION AGENT CLASS (LangGraph-based)
# ============================================================

class ApplicationAgentLangGraph(LangGraphAgent):
    """
    LangGraph-based agent for assisting with job applications.
    
    IMPORTANT: This agent is designed for human-in-the-loop operation.
    It will NEVER auto-submit applications.
    
    Capabilities:
    - Opens job application page
    - Extracts and analyzes form fields
    - Generates smart answer suggestions
    - Validates application readiness
    - Waits for human approval before any action
    """
    
    def __init__(self):
        system_prompt = """You are an intelligent job application assistant.

Your role is to help the user prepare job applications by:
1. Analyzing application form fields
2. Generating smart answer suggestions
3. Validating application readiness
4. Providing a summary for human review

CRITICAL RULES:
- NEVER auto-submit any applications
- Always flag uncertain answers for human review
- Prioritize accuracy over speed
- Generate professional, tailored responses

Use your tools to analyze forms and generate suggestions."""

        super().__init__("application", system_prompt)
        
        # Register tools
        self.add_tool(analyze_form_fields)
        self.add_tool(generate_answer_suggestion)
        self.add_tool(validate_application_readiness)
        self.add_tool(generate_application_summary)
    
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
    
    async def prepare_application(
        self,
        job_url: str,
        company: str = "",
        role: str = "",
    ) -> Dict[str, Any]:
        """
        Prepare application by analyzing the job page.
        
        This opens the page, extracts information, but DOES NOT submit anything.
        
        Args:
            job_url: URL of the job posting
            company: Company name for context
            role: Job role for context
            
        Returns:
            Application preparation data
        """
        self.logger.info(f"Preparing application for: {job_url}")
        
        preparation = {
            "job_url": job_url,
            "company": company,
            "role": role,
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
                
                # Analyze form fields using tool
                analysis = analyze_form_fields.invoke({"fields_data": fields})
                preparation["field_analysis"] = analysis
                
                # Generate suggestions for text fields
                for field in fields:
                    if field.get("label") and field.get("type") in ["text", "textarea"]:
                        suggestion = generate_answer_suggestion.invoke({
                            "question": field["label"],
                            "field_type": field["type"],
                            "job_role": role,
                            "company": company,
                        })
                        preparation["suggested_answers"].append({
                            "field": field["name"] or field["label"],
                            **suggestion,
                        })
                
                # Validate readiness
                validation = validate_application_readiness.invoke({
                    "form_fields": fields,
                    "suggested_answers": preparation["suggested_answers"],
                })
                preparation["validation"] = validation
                
                # Generate summary
                summary = generate_application_summary.invoke({
                    "company": company,
                    "role": role,
                    "form_fields_count": len(fields),
                    "suggestions_count": len(preparation["suggested_answers"]),
                })
                preparation["summary"] = summary
                
                # Take screenshot for reference
                try:
                    await page.screenshot(path=f"logs/application_{hash(job_url)}.png")
                except:
                    pass  # Screenshot is optional
                
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
                prep = await self.prepare_application(
                    job_url=job.get("job_url", ""),
                    company=job.get("company", ""),
                    role=job.get("role", ""),
                )
                preparations.append(prep)
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


    async def fill_application_form(
        self,
        job_url: str,
        fields_map: Dict[str, str],
        submit: bool = False, # SAFETY: Default to Dry Run
    ) -> Dict[str, Any]:
        """
        Auto-fill application form with user data.
        
        Args:
            job_url: Job URL
            fields_map: Map of field names to values
            submit: Whether to click submit (DANGEROUS)
            
        Returns:
            Status of the operation
        """
        self.logger.info(f"Auto-filling application (Submit={submit}): {job_url}")
        
        try:
            async with playwright_manager.get_page() as page:
                await playwright_manager.navigate(page, job_url)
                
                # Fill mapped fields with human simulation
                for name, value in fields_map.items():
                    try:
                        # Try exact name match first
                        selector = f"[name='{name}']"
                        if await page.query_selector(selector):
                            await playwright_manager.fill(page, selector, value)
                            continue
                            
                        # Try label match (Smart fallback)
                        # This is where we'd use SmartDiscovery in future
                    except Exception as e:
                        self.logger.warning(f"Failed to fill field {name}: {e}")
                
                # Take proof screenshot
                screenshot_path = f"logs/filled_{hash(job_url)}.png"
                await playwright_manager.screenshot(page, screenshot_path)
                
                if submit:
                    self.logger.warning(f"⚠️ ATTEMPTING SUBMISSION FOR {job_url}")
                    # Strict click logic for submit buttons
                    submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
                    if submit_btn:
                        await playwright_manager.click(page, "button[type='submit']")
                        await page.wait_for_timeout(5000)
                        return {"status": "submitted", "proof": screenshot_path}
                    else:
                        return {"status": "failed", "error": "Submit button not found"}
                else:
                    self.logger.info("ℹ️ Dry Run: Skipping submission click")
                    return {"status": "filled_dry_run", "proof": screenshot_path}
                    
        except Exception as e:
            self.logger.error(f"Auto-fill failed: {e}")
            return {"status": "error", "error": str(e)}

# Export singleton and class
application_agent = ApplicationAgentLangGraph()
ApplicationAgent = ApplicationAgentLangGraph
