"""
Intelligent Tracking Agent - LangGraph-based application tracking
Manages job applications with comprehensive tools
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.config.constants import ApplicationStatus, SHEETS_COLUMNS
from app.config.settings import get_settings
from app.tools.sheets import sheets_client, JobApplication, FollowUp
from app.tools.utils.logger import get_logger


# ============================================================
# TRACKING TOOLS
# ============================================================

@tool
def log_new_application(
    company: str,
    role: str,
    platform: str,
    job_url: str,
    fit_score: int,
    location: str = "",
    experience_required: str = "",
    job_description: str = "",
    interview_prep: str = "",
    skills_to_learn: str = "",
) -> Dict[str, Any]:
    """
    Log a new job application to tracking sheet.
    
    Args:
        company: Company name
        role: Job title
        platform: Where the job was found
        job_url: URL to job posting
        fit_score: Calculated fit score (0-100)
        location: Job location
        experience_required: Experience requirement
        job_description: Full JD text
        interview_prep: Interview prep summary
        skills_to_learn: Skills to learn for this role
        
    Returns:
        Success status and row number
    """
    try:
        application = JobApplication(
            date=datetime.now().strftime("%Y-%m-%d"),
            platform=platform,
            company=company,
            role=role,
            location=location,
            experience_required=experience_required,
            fit_score=fit_score,
            status=ApplicationStatus.DISCOVERED,
            job_url=job_url,
            job_description=job_description[:500] if job_description else "",
            interview_prep=interview_prep,
            skills_to_learn=skills_to_learn,
            notes="",
        )
        
        sheets_client.add_application(application)
        
        return {
            "success": True,
            "message": f"Logged application for {role} at {company}",
            "company": company,
            "role": role,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
def update_application_status(
    company: str,
    role: str,
    new_status: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Update an application's status.
    
    Args:
        company: Company name
        role: Job role
        new_status: New status (applied, interview, rejected, offer, no_response)
        notes: Additional notes
        
    Returns:
        Success status
    """
    try:
        # Validate status
        valid_statuses = ["discovered", "scored", "applied", "interview", 
                        "rejected", "offer", "no_response", "pending_approval"]
        if new_status.lower() not in valid_statuses:
            return {"success": False, "error": f"Invalid status: {new_status}"}
        
        status = ApplicationStatus(new_status.lower())
        sheets_client.update_status(company, role, status, notes)
        
        return {
            "success": True,
            "message": f"Updated {company} - {role} to {new_status}",
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_application_statistics() -> Dict[str, Any]:
    """
    Get comprehensive application statistics.
    
    Returns:
        Statistics including totals, rates, and status breakdown
    """
    try:
        applications = sheets_client.get_all_applications()
        
        stats = {
            "total_discovered": 0,
            "total_applied": 0,
            "interviews": 0,
            "offers": 0,
            "rejected": 0,
            "no_response": 0,
            "pending": 0,
        }
        
        platform_breakdown = {}
        avg_score = 0
        total_score = 0
        
        for app in applications:
            stats["total_discovered"] += 1
            
            status = app.status.value if hasattr(app.status, 'value') else str(app.status)
            
            if status in ["applied", "interview", "offer", "rejected", "no_response"]:
                stats["total_applied"] += 1
            if status == "interview":
                stats["interviews"] += 1
            elif status == "offer":
                stats["offers"] += 1
            elif status == "rejected":
                stats["rejected"] += 1
            elif status == "no_response":
                stats["no_response"] += 1
            elif status in ["discovered", "scored", "pending_approval"]:
                stats["pending"] += 1
            
            # Platform breakdown
            platform = app.platform
            platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
            
            # Average score
            total_score += app.fit_score
        
        if stats["total_discovered"] > 0:
            avg_score = round(total_score / stats["total_discovered"], 1)
        
        # Calculate rates
        if stats["total_applied"] > 0:
            interview_rate = round(stats["interviews"] / stats["total_applied"] * 100, 1)
            offer_rate = round(stats["offers"] / stats["total_applied"] * 100, 1)
        else:
            interview_rate = 0
            offer_rate = 0
        
        return {
            "total_discovered": stats["total_discovered"],
            "total_applied": stats["total_applied"],
            "interviews": stats["interviews"],
            "offers": stats["offers"],
            "rejected": stats["rejected"],
            "no_response": stats["no_response"],
            "pending": stats["pending"],
            "interview_rate": interview_rate,
            "offer_rate": offer_rate,
            "average_fit_score": avg_score,
            "platform_breakdown": platform_breakdown,
            "success_rate": offer_rate,
        }
        
    except Exception as e:
        return {"error": str(e)}


@tool
def get_pending_followups(days_threshold: int = 7) -> Dict[str, Any]:
    """
    Get applications that need follow-up.
    
    Args:
        days_threshold: Days since applied to trigger follow-up
        
    Returns:
        List of applications needing follow-up
    """
    try:
        applications = sheets_client.get_all_applications()
        followups = []
        today = datetime.now()
        
        for app in applications:
            if app.status == ApplicationStatus.APPLIED:
                try:
                    applied_date = datetime.strptime(app.date, "%Y-%m-%d")
                    days_since = (today - applied_date).days
                    
                    if days_since >= days_threshold:
                        followups.append({
                            "company": app.company,
                            "role": app.role,
                            "applied_date": app.date,
                            "days_since": days_since,
                            "status": app.status.value,
                            "job_url": app.job_url,
                        })
                except:
                    continue
        
        # Sort by days since (oldest first)
        followups.sort(key=lambda x: x["days_since"], reverse=True)
        
        return {
            "followups": followups,
            "count": len(followups),
            "message": f"Found {len(followups)} applications needing follow-up",
        }
        
    except Exception as e:
        return {"error": str(e), "followups": []}


@tool
def generate_followup_email(
    company: str,
    role: str,
    days_since: int,
) -> Dict[str, Any]:
    """
    Generate a follow-up email for an application.
    
    Args:
        company: Company name
        role: Job role applied for
        days_since: Days since application
        
    Returns:
        Follow-up email content
    """
    # Professional follow-up template
    if days_since < 10:
        tone = "checking in"
    elif days_since < 20:
        tone = "following up"
    else:
        tone = "reaching out again"
    
    email = f"""Subject: Follow-up: {role} Application - Ajsal PV

Dear Hiring Team,

I hope this email finds you well. I am {tone} regarding my application for the {role} position at {company}, submitted {days_since} days ago.

I remain very enthusiastic about the opportunity to contribute to {company}'s AI initiatives. My experience with LangChain, RAG systems, and production LLM deployments aligns well with the requirements for this role.

Key highlights from my background:
• Built real-time AI voice agents with <500ms latency at Brevo Technologies
• Developed RAG pipelines achieving 85% retrieval accuracy
• Created automated interview systems reducing screening time by 60%

I would welcome the opportunity to discuss how my skills can benefit your team. Please let me know if you need any additional information.

Thank you for your time and consideration.

Best regards,
Ajsal PV
pvajsal27@gmail.com | +91 7356793165"""

    return {
        "company": company,
        "role": role,
        "email_subject": f"Follow-up: {role} Application - Ajsal PV",
        "email_body": email,
    }


@tool
def get_applications_by_status(status: str) -> Dict[str, Any]:
    """
    Get all applications with a specific status.
    
    Args:
        status: Status to filter by
        
    Returns:
        List of matching applications
    """
    try:
        applications = sheets_client.get_all_applications()
        matching = []
        
        for app in applications:
            app_status = app.status.value if hasattr(app.status, 'value') else str(app.status)
            if app_status.lower() == status.lower():
                matching.append({
                    "company": app.company,
                    "role": app.role,
                    "platform": app.platform,
                    "fit_score": app.fit_score,
                    "date": app.date,
                    "job_url": app.job_url,
                })
        
        return {
            "applications": matching,
            "count": len(matching),
            "status": status,
        }
        
    except Exception as e:
        return {"error": str(e), "applications": []}


@tool
def analyze_application_pipeline() -> Dict[str, Any]:
    """
    Analyze the application pipeline for insights.
    
    Returns:
        Pipeline analysis with recommendations
    """
    try:
        stats = get_application_statistics.invoke({})
        
        insights = []
        recommendations = []
        
        # Pipeline analysis
        if stats.get("total_discovered", 0) > 0:
            apply_rate = stats.get("total_applied", 0) / stats["total_discovered"] * 100
            insights.append(f"Application rate: {apply_rate:.1f}% of discovered jobs")
            
            if apply_rate < 30:
                recommendations.append("Consider applying to more discovered jobs")
        
        if stats.get("total_applied", 0) > 0:
            interview_rate = stats.get("interview_rate", 0)
            insights.append(f"Interview conversion: {interview_rate}%")
            
            if interview_rate < 10:
                recommendations.append("Improve resume targeting for better interview rates")
            elif interview_rate > 30:
                insights.append("Strong interview conversion - keep current approach")
        
        if stats.get("no_response", 0) > 5:
            recommendations.append(f"You have {stats['no_response']} pending applications - consider follow-ups")
        
        # Platform performance
        platform_breakdown = stats.get("platform_breakdown", {})
        if platform_breakdown:
            best_platform = max(platform_breakdown, key=platform_breakdown.get)
            insights.append(f"Most active platform: {best_platform}")
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "summary": f"Pipeline: {stats.get('total_discovered', 0)} discovered → "
                      f"{stats.get('total_applied', 0)} applied → "
                      f"{stats.get('interviews', 0)} interviews → "
                      f"{stats.get('offers', 0)} offers",
        }
        
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# TRACKING AGENT CLASS
# ============================================================

class TrackingAgentLangGraph(LangGraphAgent):
    """
    Intelligent tracking agent for job applications.
    
    Capabilities:
    - Log new applications with full details
    - Update application status
    - Get statistics and analytics
    - Identify follow-ups needed
    - Generate follow-up emails
    - Analyze pipeline performance
    """
    
    def __init__(self):
        system_prompt = """You are an intelligent job application tracking assistant.

Your responsibilities:
1. Track all job applications accurately
2. Monitor application statuses
3. Identify applications needing follow-up
4. Provide insights on application performance
5. Generate professional follow-up emails

Always be thorough and maintain data accuracy.
Use the tools to manage the application pipeline effectively."""

        super().__init__("tracking", system_prompt)
        
        # Register all tools
        self.add_tool(log_new_application)
        self.add_tool(update_application_status)
        self.add_tool(get_application_statistics)
        self.add_tool(get_pending_followups)
        self.add_tool(generate_followup_email)
        self.add_tool(get_applications_by_status)
        self.add_tool(analyze_application_pipeline)
    
    async def log_application(
        self,
        company: str,
        role: str,
        platform: str,
        job_url: str,
        fit_score: int,
        location: str = "",
        experience_required: str = "",
        job_description: str = "",
        interview_prep: str = "",
        skills_to_learn: str = "",
    ) -> Dict[str, Any]:
        """Log a new application"""
        return log_new_application.invoke({
            "company": company,
            "role": role,
            "platform": platform,
            "job_url": job_url,
            "fit_score": fit_score,
            "location": location,
            "experience_required": experience_required,
            "job_description": job_description,
            "interview_prep": interview_prep,
            "skills_to_learn": skills_to_learn,
        })
    
    async def update_status(
        self,
        company: str,
        role: str,
        new_status: str,
        notes: str = "",
    ) -> bool:
        """Update application status"""
        result = update_application_status.invoke({
            "company": company,
            "role": role,
            "new_status": new_status,
            "notes": notes,
        })
        return result.get("success", False)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        return get_application_statistics.invoke({})
    
    async def get_pending_followups(self, days_threshold: int = 7) -> List[Dict]:
        """Get applications needing follow-up"""
        result = get_pending_followups.invoke({"days_threshold": days_threshold})
        return result.get("followups", [])
    
    async def generate_followup(
        self,
        company: str,
        role: str,
        days_since: int,
    ) -> str:
        """Generate follow-up email"""
        result = generate_followup_email.invoke({
            "company": company,
            "role": role,
            "days_since": days_since,
        })
        return result.get("email_body", "")
    
    async def run(self, **kwargs) -> AgentResult:
        """Run tracking agent to get current pipeline status"""
        try:
            stats = await self.get_statistics()
            followups = await self.get_pending_followups()
            analysis = analyze_application_pipeline.invoke({})
            
            return self._success(
                data={
                    "statistics": stats,
                    "pending_followups": followups,
                    "pipeline_analysis": analysis,
                },
                message="Tracking data retrieved successfully"
            )
        except Exception as e:
            return self._error(str(e))


# Export singleton
tracking_agent = TrackingAgentLangGraph()
