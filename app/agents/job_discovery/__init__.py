"""
Job Discovery package initialization
"""
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.job_discovery.linkedin_agent import linkedin_agent, LinkedInAgent
from app.agents.job_discovery.indeed_agent import indeed_agent, IndeedAgent
from app.agents.job_discovery.naukri_agent import naukri_agent, NaukriAgent
from app.agents.job_discovery.glassdoor_agent import glassdoor_agent, GlassdoorAgent
from app.agents.job_discovery.instahyre_agent import instahyre_agent, InstahyreAgent
from app.agents.job_discovery.cutshort_agent import cutshort_agent, CutshortAgent
from app.agents.job_discovery.wellfound_agent import wellfound_agent, WellfoundAgent
from app.agents.job_discovery.hirist_agent import hirist_agent, HiristAgent

__all__ = [
    "IntelligentJobDiscoveryAgent",
    "linkedin_agent", "LinkedInAgent",
    "indeed_agent", "IndeedAgent",
    "naukri_agent", "NaukriAgent",
    "glassdoor_agent", "GlassdoorAgent",
    "instahyre_agent", "InstahyreAgent",
    "cutshort_agent", "CutshortAgent",
    "wellfound_agent", "WellfoundAgent",
    "hirist_agent", "HiristAgent",
]
