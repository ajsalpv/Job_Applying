"""
Cover Letter Agent - LangGraph-based with tool calling
"""
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult


# User profile for cover letters
USER_PROFILE = {
    "name": "Ajsal PV",
    "email": "pvajsal27@gmail.com",
    "phone": "+91 7356793165",
    "linkedin": "linkedin.com/in/ajsalpv",
    "github": "github.com/ajsalpv",
    "experience_years": 2,
    "current_role": "AI Developer",
    "current_company": "Brevo Technologies",
    "location": "Bangalore, India",
}


@tool
def analyze_company(company: str, job_description: str) -> Dict[str, Any]:
    """
    Analyze company from job description to personalize cover letter.
    
    Args:
        company: Company name
        job_description: Job description text
        
    Returns:
        Company insights
    """
    jd_lower = job_description.lower()
    
    # Detect company characteristics
    insights = {
        "name": company,
        "likely_startup": any(kw in jd_lower for kw in ["startup", "fast-paced", "agile", "equity"]),
        "likely_enterprise": any(kw in jd_lower for kw in ["enterprise", "scale", "fortune", "global"]),
        "remote_friendly": any(kw in jd_lower for kw in ["remote", "wfh", "distributed"]),
        "ai_focused": any(kw in jd_lower for kw in ["ai-first", "ml-driven", "ai company"]),
    }
    
    # Generate hooks
    hooks = []
    if insights["likely_startup"]:
        hooks.append(f"I'm excited about {company}'s innovative approach")
    if insights["ai_focused"]:
        hooks.append(f"As an AI-first company, {company} aligns perfectly with my passion")
    if not hooks:
        hooks.append(f"I'm drawn to {company}'s mission and culture")
    
    return {
        "insights": insights,
        "hooks": hooks,
    }


@tool
def match_skills_to_requirements(required_skills: List[str]) -> Dict[str, Any]:
    """
    Match user skills to job requirements.
    
    Args:
        required_skills: Skills mentioned in JD
        
    Returns:
        Matching skills and talking points
    """
    user_skills = {
        "python": "2+ years of Python development",
        "langchain": "Built production RAG and LLM systems with LangChain",
        "llm": "Developed AI voice agents and chatbots using LLMs",
        "rag": "Implemented FAISS-based retrieval systems with 85% accuracy",
        "nlp": "Created NER systems using BERT and SpaCy",
        "fastapi": "Designed RESTful APIs serving 10K+ requests daily",
        "tensorflow": "Applied deep learning for text classification",
        "groq": "Built real-time AI systems with Groq inference",
    }
    
    matches = []
    talking_points = []
    
    for skill in required_skills:
        skill_lower = skill.lower()
        for key, value in user_skills.items():
            if key in skill_lower:
                matches.append(skill)
                talking_points.append(value)
                break
    
    return {
        "matching_skills": matches,
        "talking_points": talking_points[:4],  # Top 4
    }


@tool
def generate_cover_letter_paragraphs(
    company: str,
    role: str,
    hooks: List[str],
    talking_points: List[str],
) -> Dict[str, Any]:
    """
    Generate cover letter paragraphs.
    
    Args:
        company: Company name
        role: Job role
        hooks: Personalized hooks for opening
        talking_points: Skills talking points
        
    Returns:
        Cover letter paragraphs
    """
    opening = f"""Dear Hiring Manager,

{hooks[0] if hooks else f"I am excited to apply for the {role} position at {company}"}. With 2 years of experience building production AI systems at Brevo Technologies, I believe I can make an immediate impact on your team."""

    skills_para = f"""In my current role, I {talking_points[0] if talking_points else "developed AI solutions using modern frameworks"}. {talking_points[1] if len(talking_points) > 1 else "I also have experience with LangChain and RAG systems"}. These experiences have equipped me with practical skills in taking AI projects from concept to production."""

    projects_para = """Recently, I built a multilingual real-time AI voice agent using Groq and LangChain with <500ms latency, demonstrating my ability to deliver performant AI solutions. I also developed an automated interviewing platform that reduced screening time by 60%, showcasing my focus on business impact."""

    closing = f"""I am particularly excited about this opportunity because it aligns with my passion for building practical AI applications. I would welcome the chance to discuss how my experience can contribute to {company}'s AI initiatives.

Thank you for considering my application. I look forward to the opportunity to speak with you.

Best regards,
{USER_PROFILE['name']}
{USER_PROFILE['email']} | {USER_PROFILE['phone']}"""

    return {
        "paragraphs": {
            "opening": opening,
            "skills": skills_para,
            "projects": projects_para,
            "closing": closing,
        },
        "full_letter": f"{opening}\n\n{skills_para}\n\n{projects_para}\n\n{closing}",
    }


class CoverLetterAgentLangGraph(LangGraphAgent):
    """
    LangGraph-based cover letter generation agent.
    """
    
    def __init__(self):
        system_prompt = """You are an expert cover letter writer for AI/ML roles.
Generate personalized, compelling cover letters that:
1. Hook the reader with company-specific insights
2. Highlight relevant skills and experiences
3. Demonstrate enthusiasm and culture fit
4. Keep it concise (under 300 words)

Use the tools to analyze the company and match skills before generating."""

        super().__init__("cover_letter", system_prompt)
        
        self.add_tool(analyze_company)
        self.add_tool(match_skills_to_requirements)
        self.add_tool(generate_cover_letter_paragraphs)
    
    async def generate_cover_letter(
        self,
        company: str,
        role: str,
        job_description: str,
    ) -> str:
        """
        Generate personalized cover letter.
        """
        # Analyze company
        company_analysis = analyze_company.invoke({
            "company": company,
            "job_description": job_description,
        })
        
        # Extract skills from JD (simple extraction)
        jd_lower = job_description.lower()
        skills = []
        for skill in ["python", "langchain", "llm", "rag", "nlp", "fastapi", "tensorflow", "groq"]:
            if skill in jd_lower:
                skills.append(skill)
        
        # Match skills
        skills_match = match_skills_to_requirements.invoke({
            "required_skills": skills,
        })
        
        # Generate letter
        letter_result = generate_cover_letter_paragraphs.invoke({
            "company": company,
            "role": role,
            "hooks": company_analysis.get("hooks", []),
            "talking_points": skills_match.get("talking_points", []),
        })
        
        return letter_result.get("full_letter", "")
    
    async def run(
        self,
        jobs: List[Dict[str, Any]],
    ) -> AgentResult:
        """
        Generate cover letters for multiple jobs.
        """
        self.logger.info(f"Generating cover letters for {len(jobs)} jobs")
        
        results = []
        
        for job in jobs:
            try:
                letter = await self.generate_cover_letter(
                    company=job.get("company", ""),
                    role=job.get("role", ""),
                    job_description=job.get("job_description", ""),
                )
                
                results.append({
                    "company": job.get("company"),
                    "role": job.get("role"),
                    "cover_letter": letter,
                })
                
            except Exception as e:
                self.logger.error(f"Error for {job.get('company')}: {e}")
                continue
        
        return self._success(
            data={"cover_letters": results},
            message=f"Generated cover letters for {len(results)} jobs"
        )


cover_letter_agent = CoverLetterAgentLangGraph()
# Export as default cover letter agent
CoverLetterAgent = CoverLetterAgentLangGraph
