from typing import Dict, Any, List, Optional
from datetime import datetime
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.tools.utils.logger import get_logger
from app.tools.notifications.telegram_notifier import notifier

logger = get_logger("supervisor")


class SupervisorAgentLangGraph(LangGraphAgent):
    """
    Supervisor Agent - Monitors all discovery agents, tracks health, and auto-heals.
    Inherits from LangGraphAgent for architectural consistency.
    """
    
    def __init__(self):
        system_prompt = """You are the Supervisor Agent responsible for system health.
Your job is to monitor scrape success/failure rates, jobs discovered, and platform health.
If a platform fails repeatedly, you must disable it to protect the system.
You can also re-enable platforms when requested."""
        
        super().__init__("supervisor", system_prompt)
        self.health_data = {}  # platform -> {failures, success_count, last_error, status}
        self.max_failures = 3

    def is_platform_active(self, platform: str) -> bool:
        """Check if a platform is currently active"""
        data = self.health_data.get(platform, {"status": "active"})
        return data.get("status") == "active"

    def record_success(self, platform: str, jobs_found: int, duration: float):
        """Record a successful scrape session"""
        if platform not in self.health_data:
            self.health_data[platform] = {
                "failures": 0, 
                "success_count": 0, 
                "total_jobs": 0,
                "status": "active",
                "avg_duration": 0
            }
        
        data = self.health_data[platform]
        data["failures"] = 0  # Reset on success
        data["success_count"] += 1
        data["total_jobs"] += jobs_found
        data["last_success"] = str(datetime.now())
        data["status"] = "active"
        
        # Simple moving average for duration
        if data["avg_duration"] == 0:
            data["avg_duration"] = duration
        else:
            data["avg_duration"] = (data["avg_duration"] * 0.7) + (duration * 0.3)
        
        logger.info(f"✅ Supervisor: {platform} recorded success ({jobs_found} jobs)")

    def record_failure(self, platform: str, error: str, duration: float):
        """Record a platform failure and auto-disable if needed"""
        if platform not in self.health_data:
            self.health_data[platform] = {
                "failures": 0, 
                "success_count": 0, 
                "total_jobs": 0,
                "status": "active",
                "avg_duration": 0
            }
        
        data = self.health_data[platform]
        data["failures"] += 1
        data["last_error"] = str(error)
        data["last_failure_time"] = str(datetime.now())
        
        logger.warning(f"⚠️ Supervisor: {platform} failure #{data['failures']}: {error}")
        
        if data["failures"] >= self.max_failures:
            data["status"] = "disabled"
            logger.error(f"🚫 Supervisor: AUTO-DISABLING {platform} after {self.max_failures} failures.")
            # Notify user via Telegram
            self._notify_disabling(platform, error)

    def _notify_disabling(self, platform: str, error: str):
        """Send Telegram alert about disabled platform"""
        try:
            import asyncio
            msg = (
                f"🚨 *Supervisor Alert*\n"
                f"Platform *{platform.upper()}* has been automatically *DISABLED*.\n"
                f"Reason: {self.max_failures} consecutive failures.\n"
                f"Last Error: `{error}`\n\n"
                f"Please check logs or re-enable via mobile app."
            )
            # We use the common notifier
            asyncio.create_task(notifier.send_notification(msg))
        except Exception as e:
            logger.error(f"Failed to send supervisor notification: {e}")

    def re_enable_platform(self, platform: str):
        """Manually re-enable a platform"""
        if platform in self.health_data:
            self.health_data[platform]["status"] = "active"
            self.health_data[platform]["failures"] = 0
            logger.info(f"🔄 Supervisor: Platform {platform} re-enabled manually.")
            return True
        return False

    def get_health_report(self) -> Dict[str, Any]:
        """Get summary of all platform health for the UI"""
        return {
            "timestamp": str(datetime.now()),
            "platforms": self.health_data
        }

    async def run(self, **kwargs) -> AgentResult:
        """Main entry for LangGraph-based status reporting"""
        return self._success(data=self.get_health_report())


# Singleton instance
supervisor = SupervisorAgentLangGraph()
