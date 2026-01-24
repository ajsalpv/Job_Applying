"""
Constants - Enums and fixed values used across the application
"""
from enum import Enum
from typing import Dict


class JobPlatform(str, Enum):
    """Supported job platforms"""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    NAUKRI = "naukri"
    GLASSDOOR = "glassdoor"
    INSTAHYRE = "instahyre"
    CUTSHORT = "cutshort"
    WELLFOUND = "wellfound"  # formerly AngelList
    HIRIST = "hirist"
    CAREER_SITE = "career_site"


class ApplicationStatus(str, Enum):
    """Job application status tracking"""
    DISCOVERED = "discovered"
    SCORED = "scored"
    RESUME_GENERATED = "resume_generated"
    PENDING_APPROVAL = "pending_approval"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"
    OFFER = "offer"


class AgentType(str, Enum):
    """Types of agents in the system"""
    DISCOVERY = "discovery"
    SCORING = "scoring"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    APPLICATION = "application"
    TRACKING = "tracking"


# Scoring weights for job fit calculation
SCORING_WEIGHTS: Dict[str, float] = {
    "skill_match": 0.40,      # 40%
    "experience_match": 0.25,  # 25%
    "location_match": 0.15,    # 15%
    "role_relevance": 0.20,    # 20%
}


# User skills for matching (based on Ajsal's resume)
USER_SKILLS = [
    # Core
    "Python", "Machine Learning", "Deep Learning", "NLP",
    # LLM & AI
    "LLM", "Large Language Models", "LangChain", "RAG",
    "Prompt Engineering", "Groq", "Hugging Face",
    # Frameworks
    "TensorFlow", "Keras", "Scikit-Learn", "FastAPI",
    "NumPy", "Pandas", "Transformer", "PyTorch",
    # Tools
    "n8n", "Vocode", "Deepgram", "FAISS", "Vector Database",
    # General
    "AI", "Artificial Intelligence", "API Development",
    "Backend Development", "Node.js", "GenAI", "Generative AI",
]

# Skills to EXCLUDE (we don't want Computer Vision roles)
EXCLUDED_SKILLS = [
    "Computer Vision", "CV", "OpenCV", "Image Processing",
    "Object Detection", "YOLO", "Image Recognition",
    "Video Processing", "Image Classification",
]

# Experience configuration
USER_EXPERIENCE_YEARS = 1  # Updated to 1 year
# Maximum experience range to consider (will accept 0-2 years roles)
MAX_EXPERIENCE_ACCEPTABLE = 2


# Target job titles (AI/ML focused, NO Computer Vision)
TARGET_JOB_TITLES = [
    "AI Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Developer",
    "LLM Engineer",
    "NLP Engineer",
    "Deep Learning Engineer",
    "Data Scientist",
    "Applied ML Engineer",
    "AI/ML Engineer",
    "GenAI Engineer",
    "Generative AI Engineer",
    "ML Developer",
    "Machine Learning Developer",
    "Conversational AI Engineer",
    "AI Research Engineer",
]

# Job titles to EXCLUDE
EXCLUDED_JOB_TITLES = [
    "Computer Vision Engineer",
    "CV Engineer",
    "Image Processing Engineer",
    "Video AI Engineer",
]


# Location preferences (User can apply to these cities)
PREFERRED_LOCATIONS = [
    # Highest Priority
    "Remote", "Work from Home", "WFH", "Hybrid",
    
    # High Priority Cities
    "Bangalore", "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Kochi", "Cochin",
    "Calicut", "Kozhikode",
    "Trivandrum", "Thiruvananthapuram",
    "Mohali",
    
    # General
    "India",
]


# Platform-specific URLs
PLATFORM_URLS = {
    JobPlatform.LINKEDIN: "https://www.linkedin.com/jobs/search/",
    JobPlatform.INDEED: "https://in.indeed.com/jobs",
    JobPlatform.NAUKRI: "https://www.naukri.com/",
    JobPlatform.GLASSDOOR: "https://www.glassdoor.co.in/Job/",
    JobPlatform.INSTAHYRE: "https://www.instahyre.com/",
    JobPlatform.CUTSHORT: "https://cutshort.io/",
    JobPlatform.WELLFOUND: "https://wellfound.com/",
    JobPlatform.HIRIST: "https://www.hirist.tech/",
}


# Google Sheets column structure (with JD and Interview Prep)
SHEETS_COLUMNS = {
    "applications": [
        "Date", "Platform", "Company", "Role", "Location",
        "Experience Required", "Fit Score", "Status", "Job URL",
        "Job Description", "Interview Prep", "Skills to Learn", "Notes"
    ],
    "metrics": [
        "Total Discovered", "Total Applied", "Interviews",
        "Rejections", "Offers", "Success Rate"
    ],
    "followups": [
        "Company", "Role", "Applied Date", "Days Since Applied",
        "Status", "Action Needed", "Next Follow-up"
    ],
}
