"""
Interview Prep Agent - LangGraph-based with tool calling
Generates interview preparation based on job requirements
"""
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.config.constants import TARGET_JOB_TITLES, USER_SKILLS


# Define tools for interview prep
@tool
def get_technical_topics(role: str, skills_required: List[str]) -> Dict[str, Any]:
    """
    Get priority technical topics to study for interview.
    
    Args:
        role: Job title/role
        skills_required: Skills mentioned in JD
        
    Returns:
        List of topics with priority
    """
    role_lower = role.lower()
    topics = []
    
    # LLM/GenAI roles
    if any(kw in role_lower for kw in ["llm", "genai", "generative"]):
        topics.extend([
            {"topic": "Transformer Architecture & Attention Mechanisms", "priority": "High"},
            {"topic": "Prompt Engineering Best Practices", "priority": "High"},
            {"topic": "RAG (Retrieval Augmented Generation)", "priority": "High"},
            {"topic": "Fine-tuning vs Few-shot Learning", "priority": "Medium"},
            {"topic": "LLM Evaluation Metrics (BLEU, ROUGE, Perplexity)", "priority": "Medium"},
            {"topic": "Vector Databases (FAISS, Pinecone, Weaviate)", "priority": "Medium"},
        ])
    
    # ML Engineer roles
    if any(kw in role_lower for kw in ["ml", "machine learning"]):
        topics.extend([
            {"topic": "ML Fundamentals (Regression, Classification, Clustering)", "priority": "High"},
            {"topic": "Model Evaluation (Precision, Recall, F1, AUC-ROC)", "priority": "High"},
            {"topic": "Feature Engineering & Selection", "priority": "Medium"},
            {"topic": "Hyperparameter Tuning (Grid Search, Bayesian)", "priority": "Medium"},
            {"topic": "ML Pipeline Design & MLOps", "priority": "Medium"},
        ])
    
    # NLP roles
    if "nlp" in role_lower:
        topics.extend([
            {"topic": "NLP Pipeline (Tokenization, Embeddings, Transformers)", "priority": "High"},
            {"topic": "Named Entity Recognition (NER)", "priority": "High"},
            {"topic": "Text Classification & Sentiment Analysis", "priority": "Medium"},
            {"topic": "Language Models (BERT, GPT, T5)", "priority": "High"},
        ])
    
    # Deep Learning
    if "deep learning" in role_lower:
        topics.extend([
            {"topic": "Neural Network Architectures (CNN, RNN, Transformer)", "priority": "High"},
            {"topic": "Optimization Algorithms (Adam, SGD, Learning Rate)", "priority": "Medium"},
            {"topic": "Regularization (Dropout, BatchNorm, L1/L2)", "priority": "Medium"},
        ])
    
    # Add skills-based topics
    skill_topics = {
        "langchain": {"topic": "LangChain Framework & LCEL", "priority": "High"},
        "pytorch": {"topic": "PyTorch Fundamentals", "priority": "Medium"},
        "tensorflow": {"topic": "TensorFlow/Keras", "priority": "Medium"},
        "fastapi": {"topic": "FastAPI & REST API Design", "priority": "Medium"},
        "docker": {"topic": "Docker & Containerization", "priority": "Low"},
        "kubernetes": {"topic": "Kubernetes Basics", "priority": "Low"},
    }
    
    for skill in skills_required:
        skill_lower = skill.lower()
        if skill_lower in skill_topics:
            topics.append(skill_topics[skill_lower])
    
    # Remove duplicates and limit
    seen = set()
    unique_topics = []
    for t in topics:
        if t["topic"] not in seen:
            seen.add(t["topic"])
            unique_topics.append(t)
    
    return {"topics": unique_topics[:10], "count": len(unique_topics[:10])}


@tool
def get_expected_questions(role: str) -> Dict[str, Any]:
    """
    Get expected interview questions based on role.
    
    Args:
        role: Job title
        
    Returns:
        List of expected questions by category
    """
    role_lower = role.lower()
    questions = []
    
    # Technical questions
    if any(kw in role_lower for kw in ["ai", "ml", "llm", "nlp"]):
        questions.extend([
            {"type": "Technical", "question": "Explain how transformer attention mechanism works"},
            {"type": "Technical", "question": "What's the difference between fine-tuning and RAG?"},
            {"type": "Technical", "question": "How would you evaluate an LLM's performance?"},
            {"type": "Technical", "question": "Explain overfitting and how to prevent it"},
        ])
    
    # System Design
    questions.extend([
        {"type": "System Design", "question": "Design a real-time recommendation system"},
        {"type": "System Design", "question": "How would you build a scalable chatbot?"},
        {"type": "System Design", "question": "Design an ML pipeline for production"},
    ])
    
    # Behavioral
    questions.extend([
        {"type": "Behavioral", "question": "Tell me about a challenging ML project you worked on"},
        {"type": "Behavioral", "question": "How do you handle ambiguous requirements?"},
        {"type": "Behavioral", "question": "Describe a time you had to debug a complex model issue"},
    ])
    
    # Coding
    questions.extend([
        {"type": "Coding", "question": "Implement a basic attention mechanism in Python"},
        {"type": "Coding", "question": "Write a function to calculate cosine similarity"},
        {"type": "Coding", "question": "LeetCode Medium - Array/String manipulation"},
    ])
    
    return {"questions": questions, "count": len(questions)}


@tool
def identify_skill_gaps(job_skills: List[str]) -> Dict[str, Any]:
    """
    Identify skills to learn before interview.
    
    Args:
        job_skills: Skills required by job
        
    Returns:
        Skills to learn with priority
    """
    user_skills_lower = [s.lower() for s in USER_SKILLS]
    skills_to_learn = []
    
    for skill in job_skills:
        skill_lower = skill.lower()
        if skill_lower not in user_skills_lower:
            # Prioritize based on importance
            priority = "Medium"
            if any(kw in skill_lower for kw in ["langchain", "llm", "rag", "python"]):
                priority = "High"
            elif any(kw in skill_lower for kw in ["docker", "aws", "gcp", "kubernetes"]):
                priority = "Low"
            
            skills_to_learn.append({
                "skill": skill,
                "priority": priority,
                "suggestion": f"Learn basics of {skill}",
            })
    
    # Sort by priority
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    skills_to_learn.sort(key=lambda x: priority_order.get(x["priority"], 1))
    
    return {"skills_to_learn": skills_to_learn[:8], "count": len(skills_to_learn[:8])}


@tool
def get_preparation_tips(company: str, role: str) -> Dict[str, Any]:
    """
    Get interview preparation tips.
    
    Args:
        company: Company name
        role: Job role
        
    Returns:
        Preparation tips
    """
    tips = [
        f"Research {company}'s tech blog, engineering posts, and recent AI initiatives",
        "Practice coding problems on LeetCode (focus on Medium difficulty)",
        "Prepare 2-3 detailed project explanations with STAR method",
        "Review system design basics for AI/ML systems",
        "Brush up on Python fundamentals and common libraries (NumPy, Pandas)",
        "Prepare questions to ask the interviewer about the team and projects",
        "Review your resume and be ready to explain every point in detail",
        "Practice explaining technical concepts in simple terms",
    ]
    
    # Add role-specific tips
    role_lower = role.lower()
    if "llm" in role_lower or "genai" in role_lower:
        tips.insert(0, "Study recent LLM papers and industry trends (GPT-4, Claude, Gemini)")
        tips.insert(1, "Be ready to discuss prompt engineering strategies")
    
    return {
        "tips": tips[:10],
        "estimated_prep_time": "1-2 weeks",
        "focus_areas": ["Technical Knowledge", "Coding Practice", "System Design", "Behavioral Stories"],
    }


class InterviewPrepAgentLangGraph(LangGraphAgent):
    """
    LangGraph-based interview preparation agent.
    
    Uses tools to generate comprehensive prep guides.
    """
    
    def __init__(self):
        system_prompt = """You are an expert technical interview coach for AI/ML roles.
Given job details, you help candidates prepare for interviews by:
1. Identifying key technical topics to study
2. Predicting likely interview questions
3. Finding skill gaps to address
4. Providing actionable preparation tips

Use the available tools to gather information and provide comprehensive guidance."""

        super().__init__("interview_prep", system_prompt)
        
        # Register tools
        self.add_tool(get_technical_topics)
        self.add_tool(get_expected_questions)
        self.add_tool(identify_skill_gaps)
        self.add_tool(get_preparation_tips)
    
    async def generate_prep_guide(
        self,
        company: str,
        role: str,
        job_description: str = "",
        skills_required: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive interview prep guide.
        """
        skills = skills_required or []
        
        # Use tools directly for speed
        topics_result = get_technical_topics.invoke({
            "role": role,
            "skills_required": skills,
        })
        
        questions_result = get_expected_questions.invoke({"role": role})
        
        gaps_result = identify_skill_gaps.invoke({"job_skills": skills})
        
        tips_result = get_preparation_tips.invoke({
            "company": company,
            "role": role,
        })
        
        return {
            "company": company,
            "role": role,
            "key_topics": topics_result.get("topics", []),
            "expected_questions": questions_result.get("questions", []),
            "skills_to_learn": [s["skill"] for s in gaps_result.get("skills_to_learn", [])],
            "preparation_tips": tips_result.get("tips", []),
            "estimated_prep_time": tips_result.get("estimated_prep_time", "1-2 weeks"),
            "summary": f"Focus on {len(topics_result.get('topics', []))} key topics, "
                      f"practice {len(questions_result.get('questions', []))} question types, "
                      f"and learn {len(gaps_result.get('skills_to_learn', []))} new skills.",
        }
    
    async def run(
        self,
        jobs: List[Dict[str, Any]],
    ) -> AgentResult:
        """
        Generate interview prep for multiple jobs.
        """
        self.logger.info(f"Generating interview prep for {len(jobs)} jobs")
        
        results = []
        
        for job in jobs:
            try:
                prep = await self.generate_prep_guide(
                    company=job.get("company", ""),
                    role=job.get("role", ""),
                    job_description=job.get("job_description", ""),
                    skills_required=job.get("skills_required", []),
                )
                
                results.append({
                    "company": job.get("company"),
                    "role": job.get("role"),
                    "job_url": job.get("job_url"),
                    "interview_prep": prep,
                })
                
            except Exception as e:
                self.logger.error(f"Error for {job.get('company')}: {e}")
                continue
        
        return self._success(
            data={"preparations": results},
            message=f"Generated interview prep for {len(results)} jobs"
        )


# Export as default
interview_prep_agent = InterviewPrepAgentLangGraph()
InterviewPrepAgent = InterviewPrepAgentLangGraph
