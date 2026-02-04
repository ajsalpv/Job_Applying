"""
Naukri.com Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class NaukriAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent Naukri.com job discovery agent.
    India's largest job portal.
    """
    
    def __init__(self):
        super().__init__(
            platform="naukri",
            base_url=PLATFORM_URLS.get(JobPlatform.NAUKRI, "https://www.naukri.com/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Naukri-specific job discovery"""
        self.logger.info(f"Naukri search: {keywords} in {location}")
        
        await rate_limiter.acquire("naukri")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                keyword_slug = keywords.lower().replace(" ", "-")
                location_slug = location.lower().replace(" ", "-")
                
                # experience=0-2 (Fresher/Junior)
                # footer_freshness=7 (Last 7 days)
                search_url = (
                    f"https://www.naukri.com/{keyword_slug}-jobs-in-{location_slug}"
                    f"?experience=0&experience=1&experience=2&footer_freshness=7" # Last 7 days
                )
                
                # Use domcontentloaded for faster initial state, then wait specifically
                await playwright_manager.navigate(page, search_url, wait_for="domcontentloaded")
                await page.wait_for_timeout(6000)
                
                # FALLBACK: If title is empty, it might be a block or slow load
                title = await page.title()
                if not title or title.strip() == "":
                    self.logger.warning("Naukri: Empty title detected, attempting one reload...")
                    await page.reload(wait_until="domcontentloaded")
                    await page.wait_for_timeout(6000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        // Naukri updated layout: .srp-job-tuple, .cust-job-tuple, etc.
                        const cards = document.querySelectorAll('.jobTuple, .cust-job-tuple, article.jobTuple, .srp-job-tuple, [class*="job-tuple"]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 50) {
                                // Modern Naukri selectors often use data-testid or specific classes
                                const titleEl = card.querySelector('.title, .jobTitle, a.title, [class*="title"]');
                                const companyEl = card.querySelector('.companyInfo a, .comp-name, .name, [class*="company"]');
                                const locationEl = card.querySelector('.location, .locWdth, .loc span, [class*="location"]');
                                const expEl = card.querySelector('.experience, .expwdth, .exp span, [class*="experience"]');
                                const linkEl = card.querySelector('a.title, a[href*="job-listings"], a[class*="title"]');
                                const descEl = card.querySelector('.job-description, .ellipsis, .job-snippet, .job-desc');
                                const dateEl = card.querySelector('.posted-by, .jobPostDate, .postedDate, .footer');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '0-2 years',
                                        job_url: linkEl?.href || '',
                                        job_description: descEl?.textContent?.trim() || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'naukri',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                if not raw_jobs:
                    title = await page.title()
                    self.logger.warning(f"Naukri: 0 raw jobs found. Page title: '{title}'")
                    if any(kw in title.lower() for kw in ["blocked", "captcha", "security", "verify"]):
                        self.logger.error("Naukri: Bot detection/Security challenge detected!")
                
                self.logger.info(f"Naukri found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    exp_lower = job.get("experience_required", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                        
                    # Refined Junior-Friendly Filter
                    is_junior_friendly = any(kw in exp_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    has_high_exp = any(kw in exp_lower for kw in ["5", "6", "7", "8", "9", "5+", "8+"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "lead", "principal", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Naukri found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Naukri search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine learning"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Naukri",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


naukri_agent = NaukriAgent()
