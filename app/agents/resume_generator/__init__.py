"""
Resume generator package initialization
"""
from app.agents.resume_generator.resume_agent import resume_agent, ResumeAgent
from app.agents.resume_generator.cover_letter_agent import cover_letter_agent, CoverLetterAgent

__all__ = [
    "resume_agent",
    "ResumeAgent",
    "cover_letter_agent",
    "CoverLetterAgent",
]
