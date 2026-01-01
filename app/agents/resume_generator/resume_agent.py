"""
Resume Agent - LangGraph-based resume optimization with tools
"""
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.config.constants import USER_SKILLS


# User's experience summary for reference
EXPERIENCE_SUMMARY = """
AJSAL PV - AI/ML Developer (2 years experience)

WORK EXPERIENCE:
1. AI Developer @ Brevo Technologies (Jul 2024 - Present)
   - Built multilingual real-time AI voice agent using Groq, Deepgram, Vocode
   - Developed AI-powered interviewing product with n8n, LangChain, Groq
   - Created document processing system with LangChain for automated extraction

2. AI Developer @ Brototype (Jan 2024 - Jun 2024)
   - Developed LLM-powered learning system with LangChain, FastAPI, Groq
   - Built RAG pipeline using FAISS, LangChain, and NLP techniques
   - Created AI resume analyser with BERT NER, SpaCy, FastAPI

PROJECTS:
- AI Voice Agent (Real-time multilingual voice agent with LLM)
- Interviewer AI (Automated technical interviewing platform)
- DocuQ (AI document Q&A system with RAG)
- Resume Analyzer (BERT-based resume parsing)
- AI Code Reviewer (Automated code review platform)

SKILLS:
Python, LangChain, Groq, TensorFlow, Keras, NLP, RAG, FAISS, 
FastAPI, Hugging Face, n8n, Vocode, Deepgram, Vector Databases
"""


@tool
def extract_keywords_from_jd(job_description: str) -> Dict[str, Any]:
    """
    Extract important keywords from job description.
    
    Args:
        job_description: Full job description text
        
    Returns:
        Keywords categorized by type
    """
    jd_lower = job_description.lower()
    
    # Technical keywords
    tech_keywords = []
    all_tech = [
        "python", "langchain", "llm", "rag", "transformers", "pytorch", "tensorflow",
        "keras", "fastapi", "flask", "django", "nlp", "ml", "deep learning",
        "hugging face", "groq", "openai", "aws", "gcp", "azure", "docker",
        "kubernetes", "sql", "nosql", "mongodb", "postgresql", "redis",
        "vector database", "faiss", "pinecone", "git", "ci/cd"
    ]
    
    for kw in all_tech:
        if kw in jd_lower:
            tech_keywords.append(kw.title())
    
    # Action verbs
    action_keywords = []
    actions = ["build", "develop", "design", "implement", "deploy", "optimize",
               "scale", "integrate", "automate", "lead", "collaborate"]
    for action in actions:
        if action in jd_lower:
            action_keywords.append(action)
    
    # Domain terms
    domain_keywords = []
    domains = ["ai", "machine learning", "natural language", "conversational",
               "chatbot", "voice", "real-time", "production", "enterprise"]
    for domain in domains:
        if domain in jd_lower:
            domain_keywords.append(domain)
    
    return {
        "technical": tech_keywords,
        "actions": action_keywords,
        "domains": domain_keywords,
        "total_keywords": len(tech_keywords) + len(action_keywords) + len(domain_keywords),
    }


@tool
def match_experience_to_keywords(keywords: List[str]) -> Dict[str, Any]:
    """
    Match user's experience to job keywords.
    
    Args:
        keywords: Keywords from job description
        
    Returns:
        Matching experiences and bullet points
    """
    keywords_lower = [k.lower() for k in keywords]
    
    experience_matches = []
    
    # Match based on keywords
    if any(kw in keywords_lower for kw in ["langchain", "llm", "rag"]):
        experience_matches.append({
            "experience": "LLM Learning System @ Brototype",
            "bullet": "Developed LLM-powered learning system using LangChain, FastAPI, and Groq achieving 40% improvement in content delivery",
        })
        experience_matches.append({
            "experience": "RAG Pipeline @ Brototype",
            "bullet": "Built RAG pipeline using FAISS and LangChain for intelligent document retrieval with 85% accuracy",
        })
    
    if any(kw in keywords_lower for kw in ["voice", "real-time", "multilingual"]):
        experience_matches.append({
            "experience": "Voice Agent @ Brevo",
            "bullet": "Built multilingual real-time AI voice agent using Groq, Deepgram, and Vocode with <500ms latency",
        })
    
    if any(kw in keywords_lower for kw in ["nlp", "natural language", "text"]):
        experience_matches.append({
            "experience": "Resume Analyzer @ Brototype",
            "bullet": "Created AI resume analyzer using BERT NER and SpaCy for automated skill extraction with 90% precision",
        })
    
    if any(kw in keywords_lower for kw in ["fastapi", "api", "backend"]):
        experience_matches.append({
            "experience": "API Development",
            "bullet": "Designed RESTful APIs with FastAPI serving 10K+ requests/day with 99.9% uptime",
        })
    
    if any(kw in keywords_lower for kw in ["automation", "workflow", "n8n"]):
        experience_matches.append({
            "experience": "Interviewer AI @ Brevo",
            "bullet": "Developed automated interviewing platform using n8n workflows and LangChain reducing screening time by 60%",
        })
    
    if any(kw in keywords_lower for kw in ["document", "extraction", "processing"]):
        experience_matches.append({
            "experience": "Document Processing @ Brevo",
            "bullet": "Created document processing system with LangChain for automated data extraction from PDFs",
        })
    
    return {
        "matches": experience_matches,
        "count": len(experience_matches),
    }


@tool
def generate_ats_bullets(role: str, company: str, focus_areas: List[str]) -> Dict[str, Any]:
    """
    Generate ATS-optimized resume bullets.
    
    Args:
        role: Target role
        company: Target company
        focus_areas: Key areas to highlight
        
    Returns:
        Optimized bullet points
    """
    # Base bullets that can be customized
    bullet_templates = [
        "Developed {tech} solution at Brevo Technologies resulting in {metric}",
        "Built production-ready {tech} pipeline handling {scale} with {result}",
        "Led implementation of {feature} using {tech} achieving {outcome}",
        "Designed and deployed {system} reducing {problem} by {percentage}",
    ]
    
    # Specific optimized bullets based on focus
    optimized = []
    
    if "llm" in str(focus_areas).lower() or "ai" in str(focus_areas).lower():
        optimized.append("Developed LLM-powered AI solutions using LangChain and Groq, reducing response latency by 60%")
        optimized.append("Built production RAG pipelines with FAISS achieving 85% retrieval accuracy")
    
    if "voice" in str(focus_areas).lower() or "real-time" in str(focus_areas).lower():
        optimized.append("Engineered real-time voice AI system with <500ms latency supporting multilingual conversations")
    
    if "nlp" in str(focus_areas).lower():
        optimized.append("Implemented NLP solutions using BERT and SpaCy with 90%+ precision on entity extraction")
    
    if "backend" in str(focus_areas).lower() or "api" in str(focus_areas).lower():
        optimized.append("Designed scalable FastAPI services handling 10K+ daily requests with 99.9% uptime")
    
    # Add generic strong bullets
    optimized.extend([
        "Applied machine learning techniques to production systems serving enterprise clients",
        "Collaborated with cross-functional teams to deliver AI features ahead of schedule",
    ])
    
    return {
        "bullets": optimized[:6],
        "count": len(optimized[:6]),
        "targeting": f"{role} at {company}",
    }


class ResumeAgentLangGraph(LangGraphAgent):
    """
    LangGraph-based resume optimization agent.
    """
    
    def __init__(self):
        system_prompt = f"""You are an expert resume optimization AI.
Your task is to generate ATS-optimized resume content tailored to specific jobs.

CANDIDATE: Ajsal PV - AI/ML Developer with 2 years experience
{EXPERIENCE_SUMMARY}

Use the tools to:
1. Extract keywords from job descriptions
2. Match experience to those keywords
3. Generate ATS-optimized bullet points"""

        super().__init__("resume", system_prompt)
        
        self.add_tool(extract_keywords_from_jd)
        self.add_tool(match_experience_to_keywords)
        self.add_tool(generate_ats_bullets)
    
    async def generate_optimized_bullets(
        self,
        company: str,
        role: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Generate optimized resume bullets for a specific job.
        """
        # Extract keywords
        keywords_result = extract_keywords_from_jd.invoke({
            "job_description": job_description,
        })
        
        all_keywords = (
            keywords_result.get("technical", []) +
            keywords_result.get("actions", []) +
            keywords_result.get("domains", [])
        )
        
        # Match experience
        matches_result = match_experience_to_keywords.invoke({
            "keywords": all_keywords,
        })
        
        # Generate bullets
        bullets_result = generate_ats_bullets.invoke({
            "role": role,
            "company": company,
            "focus_areas": keywords_result.get("technical", []),
        })
        
        return {
            "company": company,
            "role": role,
            "keywords_found": all_keywords,
            "experience_matches": matches_result.get("matches", []),
            "optimized_bullets": bullets_result.get("bullets", []),
        }
    
    async def run(
        self,
        jobs: List[Dict[str, Any]],
    ) -> AgentResult:
        """
        Generate optimized resume for multiple jobs.
        """
        self.logger.info(f"Optimizing resume for {len(jobs)} jobs")
        
        results = []
        
        for job in jobs:
            try:
                result = await self.generate_optimized_bullets(
                    company=job.get("company", ""),
                    role=job.get("role", ""),
                    job_description=job.get("job_description", ""),
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error for {job.get('company')}: {e}")
                continue
        
        return self._success(
            data={"optimizations": results},
            message=f"Generated resume optimizations for {len(results)} jobs"
        )


resume_agent = ResumeAgentLangGraph()
ResumeAgent = ResumeAgentLangGraph
