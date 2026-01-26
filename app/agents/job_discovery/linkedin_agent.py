"""
LinkedIn Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class LinkedInAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent LinkedIn job discovery agent.
    
    Uses LangGraph with specialized tools for LinkedIn's structure.
    """
    
    def __init__(self):
        super().__init__(
            platform="linkedin",
            base_url=PLATFORM_URLS.get(JobPlatform.LINKEDIN, "https://www.linkedin.com/jobs/search/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        LinkedIn-specific job discovery with intelligent filtering.
        """
        self.logger.info(f"LinkedIn search: {keywords} in {location}")
        
        await rate_limiter.acquire("linkedin")
        
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                # LinkedIn guest search URL (more robust for headless)
                search_url = (
                    f"https://www.linkedin.com/jobs/search/?"
                    f"keywords={keywords.replace(' ', '%20')}"
                    f"&location={location.replace(' ', '%20')}"
                    f"&f_TPR=r86400"  # Last 24 hours
                    f"&position=1&pageNum=0"
                )
                
                await playwright_manager.navigate(page, search_url, wait_for="load")
                await page.wait_for_timeout(5000)
                
                # Scroll to load more jobs (LinkedIn lazily loads)
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        // Guest view selectors are often different
                        const cards = document.querySelectorAll('.base-card, .base-search-card, .job-search-card');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 40) {
                                const titleEl = card.querySelector('.base-search-card__title, .job-search-card__title, h3');
                                const companyEl = card.querySelector('.base-search-card__subtitle, .job-search-card__subtitle, .hidden-nested-link');
                                const locationEl = card.querySelector('.job-search-card__location, .base-search-card__metadata');
                                const linkEl = card.querySelector('a.base-card__full-link, a[href*="/jobs/view"]');
                                // Extract metadata snippet if available
                                const metaEl = card.querySelector('.base-search-card__metadata, .job-search-card__list-item');
                                const dateEl = card.querySelector('time.job-search-card__listdate, time.job-search-card__listdate--new');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: '',
                                        job_url: linkEl?.href || '',
                                        job_description: metaEl?.textContent?.trim() || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'linkedin',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"LinkedIn found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    desc_lower = job.get("job_description", "").lower()
                    
                    # Skip CV roles
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                    
                    # Refined Junior-Friendly Filter
                    is_junior_friendly = any(kw in desc_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    has_high_exp = any(kw in desc_lower for kw in ["5+", "8+", "10+ years", "5 years", "8 years"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead", "sr.", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                    
                    # Check relevance
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", 
                                   "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"LinkedIn found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"LinkedIn search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        """Run LinkedIn discovery"""
        if not keywords:
            keywords = "AI Engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on LinkedIn",
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                message=f"LinkedIn search failed: {e}",
            )


# Export singleton
linkedin_agent = LinkedInAgent()
