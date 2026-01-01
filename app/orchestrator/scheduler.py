"""
Scheduler - Periodic job checking
"""
import asyncio
from app.orchestrator.orchestrator import run_discovery_phase
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger

logger = get_logger("scheduler")

class Scheduler:
    """Background task scheduler"""
    
    def __init__(self):
        self._task = None
        self._running = False
        self.settings = get_settings()
        
    async def start(self):
        """Start the periodic scheduler"""
        if self._running:
            logger.warning("Scheduler already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scheduler started with {self.settings.check_interval_minutes}m interval")
        
    async def stop(self):
        """Stop the periodic scheduler"""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Scheduler stopped")
        
    async def _run_loop(self):
        """Main scheduling loop"""
        while self._running:
            try:
                logger.info("⏰ Triggering periodic job discovery...")
                
                # Run discovery phase
                search_locations = [loc.strip() for loc in self.settings.user_location.split(",")]
                await run_discovery_phase(
                    locations=search_locations,
                    keywords=self.settings.target_roles, # Also passing target roles as keywords? Or keep default?
                    # run_discovery_phase takes "keywords: str" (single string?). Let's check orchestrator signature.
                )
                
                logger.info("Periodic discovery finished")
                
            except Exception as e:
                logger.error(f"Error in scheduler execution: {e}")
                
            # Wait for next interval
            try:
                # Convert minutes to seconds
                sleep_seconds = self.settings.check_interval_minutes * 60
                await asyncio.sleep(sleep_seconds)
            except asyncio.CancelledError:
                break

# Global scheduler instance
scheduler = Scheduler()
