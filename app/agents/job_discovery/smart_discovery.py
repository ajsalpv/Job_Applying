"""
Smart Discovery Agent - Uses LLM to analyze page DOM and extract job data dynamically.
Acts as a fallback when hardcoded selectors fail.
"""
from typing import Dict, Any, List, Optional
import json
import re
from app.tools.llm.groq_client import GroqClient
from app.tools.utils.logger import get_logger

logger = get_logger("smart_discovery")

class SmartDiscoveryAgent:
    """
    Intelligent agent that can 'see' the page structure and extract data
    without relying on brittle hardcoded selectors.
    """
    
    def __init__(self):
        self.llm = GroqClient()
        
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
        # We need a smart way to reduce token usage
        clean_content = self._clean_html(page_content)
        
        prompt = f"""
        You are an expert web scraper. I will give you a snippet of HTML from a job search page ({url}).
        Your task is to identify the job listings and extract the following for EACH job found:
        - Role (Job Title)
        - Company Name
        - Location
        - Experience Required (if mentioned)
        - Job URL (href)
        
        Return the data as a pure JSON list of objects. 
        If no jobs are found, return an empty list [].
        Do not include any explanation, just the JSON.
        
        HTML Snippet:
        {clean_content[:15000]} 
        """
        
        try:
            response = await self.llm.generate(prompt)
            return self._parse_json(response)
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
