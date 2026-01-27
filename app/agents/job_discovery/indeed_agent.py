"""
Indeed India Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class IndeedAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent Indeed India job discovery agent.
    """
    
    def __init__(self):
        super().__init__(
            platform="indeed",
            base_url=PLATFORM_URLS.get(JobPlatform.INDEED, "https://in.indeed.com/jobs"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Indeed-specific job discovery"""
        self.logger.info(f"Indeed search: {keywords} in {location}")
        
        await rate_limiter.acquire("indeed")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                search_url = (
                    f"https://in.indeed.com/jobs?"
                    f"q={keywords.replace(' ', '+')}"
                    f"&l={location.replace(' ', '+')}"
                    f"&fromage=1"  # Last 24 hours
                )
                
                await playwright_manager.navigate(page, search_url, wait_for="load")
                await page.wait_for_timeout(5000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.job_seen_beacon, .jobCard, .result, [data-jk]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 40) {
                                const titleEl = card.querySelector('h2.jobTitle, .jobTitle, [id^="jobtitle"]');
                                const companyEl = card.querySelector('.companyName, [data-testid="company-name"], .company_location span[data-testid="company-name"]');
                                const locationEl = card.querySelector('.location, [data-testid="text-location"], .company_location [data-testid="text-location"]');
                                const expEl = card.querySelector('.attribute_snippet, [data-testid="attribute_snippet"], .metadata.salary-snippet-container');
                                const linkEl = card.querySelector('a[href*="/viewjob"], a.jcs-JobTitle, a[id^="job_"]');
                                const descEl = card.querySelector('.job-snippet, .job_snippet, [data-testid="job-snippet"]');
                                const dateEl = card.querySelector('.date, .myj-date, [data-testid="myJobsStateDate"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href ? (linkEl.href.startsWith('http') ? linkEl.href : 'https://in.indeed.com' + linkEl.getAttribute('href')) : '',
                                        job_description: descEl?.textContent?.trim() || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'indeed',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Indeed found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    exp_lower = job.get("experience_required", "").lower()
                    desc_lower = job.get("job_description", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                    
                    # Refined Junior-Friendly Filter
                    is_junior_friendly = any(kw in exp_lower + desc_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    has_high_exp = any(kw in exp_lower + desc_lower for kw in ["5", "6", "7", "8", "9", "5+", "8+", "10+"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead", "sr.", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Indeed found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Indeed search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "AI Engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Indeed",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


indeed_agent = IndeedAgent()
