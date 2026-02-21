"""
Smart Discovery Agent - Uses LLM to analyze page DOM and extract job data dynamically.
Acts as a fallback when hardcoded selectors fail.
"""
from typing import Dict, Any, List, Optional
import json
import re
from app.tools.llm.groq_client import groq_client
from app.tools.utils.logger import get_logger

logger = get_logger("smart_discovery")

class SmartDiscoveryAgent:
    """
    Intelligent agent that can 'see' the page structure and extract data
    without relying on brittle hardcoded selectors.
    """
    
    def __init__(self):
        self.llm = groq_client  # Use the singleton instance
        
    async def analyze_page(self, page_content: str, url: str) -> List[Dict[str, Any]]:
        """
        Analyze HTML content to extract job listings.
        
        Args:
            page_content: Raw HTML or text content of the page
            url: Page URL for context
            
        Returns:
            List of extracted job dictionaries
        """
        # Truncate content to fit context window (focus on body/main)
        clean_content = self._clean_html(page_content)
        
        system_prompt = "You are an expert web scraper that extracts structured job data from HTML. Return ONLY a valid JSON array, no explanation."
        
        user_prompt = f"""Analyze this HTML from a job search page ({url}).
Extract ALL job listings. For EACH job, return:
- "role": Job Title
- "company": Company Name
- "location": Location
- "experience_required": Experience (if mentioned, else "")
- "job_url": Full URL (href)

Return as a pure JSON array of objects. If no jobs found, return [].

HTML:
{clean_content[:12000]}"""
        
        try:
            response = await self.llm.invoke(system_prompt, user_prompt)
            jobs = self._parse_json(response)
            logger.info(f"Smart Discovery extracted {len(jobs)} jobs from {url}")
            return jobs
        except Exception as e:
            logger.error(f"Smart analysis failed: {e}")
            return []
            
    def _clean_html(self, html: str) -> str:
        """Remove scripts, styles, and extra whitespace to save tokens"""
        # Simple regex cleanup
        html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html = re.sub(r'\s+', ' ', html).strip()
        return html
        
    def _parse_json(self, text: str) -> List[Dict[str, Any]]:
        """Extract and parse JSON from LLM response"""
        try:
            # Find JSON block
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except:
            return []

smart_discovery = SmartDiscoveryAgent()
