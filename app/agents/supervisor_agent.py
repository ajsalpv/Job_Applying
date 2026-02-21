"""
Supervisor Agent - Monitors all discovery agents, tracks health, auto-heals failures.
"""
import time
from typing import Dict, Any, List
from app.tools.utils.logger import get_logger

logger = get_logger("supervisor")


class SupervisorAgent:
    """
    Central monitoring agent that oversees all job discovery scrapers.
    
    Capabilities:
    - Track success/failure per platform
    - Auto-disable failing scrapers after N consecutive failures
    - Generate health reports for Telegram/API
    """
    
    MAX_CONSECUTIVE_FAILURES = 3
    
    def __init__(self):
        self.platform_health: Dict[str, Dict[str, Any]] = {}
        self._initialize_platforms()
    
    def _initialize_platforms(self):
        platforms = ["indeed", "naukri", "hirist", "glassdoor", "wellfound", "linkedin"]
        for p in platforms:
            self.platform_health[p] = {
                "status": "active",        # active | degraded | disabled
                "total_runs": 0,
                "total_jobs_found": 0,
                "consecutive_failures": 0,
                "last_run_time": None,
                "last_run_duration": 0,
                "last_error": None,
                "last_job_count": 0,
            }
    
    def record_success(self, platform: str, job_count: int, duration: float):
        """Record a successful scraper run"""
        h = self.platform_health.get(platform, {})
        h["status"] = "active"
        h["total_runs"] = h.get("total_runs", 0) + 1
        h["total_jobs_found"] = h.get("total_jobs_found", 0) + job_count
        h["consecutive_failures"] = 0
        h["last_run_time"] = time.time()
        h["last_run_duration"] = round(duration, 2)
        h["last_error"] = None
        h["last_job_count"] = job_count
        self.platform_health[platform] = h
        logger.info(f"✅ [{platform}] Success: {job_count} jobs in {duration:.1f}s")
    
    def record_failure(self, platform: str, error: str, duration: float):
        """Record a failed scraper run"""
        h = self.platform_health.get(platform, {})
        h["total_runs"] = h.get("total_runs", 0) + 1
        h["consecutive_failures"] = h.get("consecutive_failures", 0) + 1
        h["last_run_time"] = time.time()
        h["last_run_duration"] = round(duration, 2)
        h["last_error"] = error
        h["last_job_count"] = 0
        
        if h["consecutive_failures"] >= self.MAX_CONSECUTIVE_FAILURES:
            h["status"] = "disabled"
            logger.error(f"🚫 [{platform}] DISABLED after {h['consecutive_failures']} consecutive failures")
        else:
            h["status"] = "degraded"
            logger.warning(f"⚠️ [{platform}] Failure #{h['consecutive_failures']}: {error}")
        
        self.platform_health[platform] = h
    
    def is_platform_active(self, platform: str) -> bool:
        """Check if a platform is healthy enough to run"""
        h = self.platform_health.get(platform, {})
        return h.get("status") != "disabled"
    
    def re_enable_platform(self, platform: str):
        """Manually re-enable a disabled platform"""
        if platform in self.platform_health:
            self.platform_health[platform]["status"] = "active"
            self.platform_health[platform]["consecutive_failures"] = 0
            logger.info(f"🔄 [{platform}] Re-enabled by user")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate a complete health report"""
        active = sum(1 for h in self.platform_health.values() if h["status"] == "active")
        degraded = sum(1 for h in self.platform_health.values() if h["status"] == "degraded")
        disabled = sum(1 for h in self.platform_health.values() if h["status"] == "disabled")
        total_jobs = sum(h.get("total_jobs_found", 0) for h in self.platform_health.values())
        
        return {
            "summary": {
                "active_platforms": active,
                "degraded_platforms": degraded,
                "disabled_platforms": disabled,
                "total_jobs_found": total_jobs,
            },
            "platforms": self.platform_health,
        }
    
    def get_telegram_report(self) -> str:
        """Generate a Telegram-friendly health report"""
        lines = ["🤖 *Supervisor Health Report*\n"]
        
        for name, h in self.platform_health.items():
            icon = "✅" if h["status"] == "active" else ("⚠️" if h["status"] == "degraded" else "🚫")
            lines.append(f"{icon} *{name.title()}*: {h['last_job_count']} jobs | {h['status']}")
        
        report = self.get_health_report()
        lines.append(f"\n📊 Total: {report['summary']['total_jobs_found']} jobs found")
        return "\n".join(lines)


# Singleton
supervisor = SupervisorAgent()
