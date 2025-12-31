"""
Rate Limiter - Per-platform request rate limiting
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
from app.config.settings import get_settings
from app.config.constants import JobPlatform


class RateLimiter:
    """Token bucket rate limiter for API/scraping requests"""
    
    def __init__(self):
        self.settings = get_settings()
        self._last_request: Dict[str, datetime] = defaultdict(lambda: datetime.min)
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._window_start: Dict[str, datetime] = defaultdict(datetime.now)
        
        # Requests per minute per platform
        self._limits = {
            JobPlatform.LINKEDIN: self.settings.linkedin_rate_limit,
            JobPlatform.INDEED: self.settings.indeed_rate_limit,
            JobPlatform.NAUKRI: self.settings.naukri_rate_limit,
            JobPlatform.CAREER_SITE: 20,  # Default for career sites
        }
    
    def _get_limit(self, platform: JobPlatform) -> int:
        """Get rate limit for platform"""
        return self._limits.get(platform, 10)
    
    def _reset_window_if_needed(self, platform: JobPlatform):
        """Reset the request count if window has passed"""
        now = datetime.now()
        window_start = self._window_start[platform]
        
        if now - window_start > timedelta(minutes=1):
            self._request_counts[platform] = 0
            self._window_start[platform] = now
    
    async def acquire(self, platform: JobPlatform):
        """
        Wait until a request can be made within rate limits.
        Uses a sliding window algorithm.
        """
        self._reset_window_if_needed(platform)
        
        limit = self._get_limit(platform)
        
        while self._request_counts[platform] >= limit:
            # Calculate wait time until window resets
            window_start = self._window_start[platform]
            wait_time = 60 - (datetime.now() - window_start).seconds
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._reset_window_if_needed(platform)
        
        # Add minimum delay between requests (2-5 seconds)
        last_request = self._last_request[platform]
        time_since_last = (datetime.now() - last_request).total_seconds()
        if time_since_last < 2:
            await asyncio.sleep(2 - time_since_last)
        
        # Record this request
        self._request_counts[platform] += 1
        self._last_request[platform] = datetime.now()
    
    def get_remaining(self, platform: JobPlatform) -> int:
        """Get remaining requests in current window"""
        self._reset_window_if_needed(platform)
        limit = self._get_limit(platform)
        return max(0, limit - self._request_counts[platform])


# Singleton instance
rate_limiter = RateLimiter()
