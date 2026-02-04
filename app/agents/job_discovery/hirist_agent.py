"""
Hirist Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class HiristAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Hirist.tech job discovery agent for Indian tech jobs."""
    
    def __init__(self):
        super().__init__(
            platform="hirist",
            base_url=PLATFORM_URLS.get(JobPlatform.HIRIST, "https://www.hirist.tech/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Hirist-specific job discovery"""
        self.logger.info(f"Hirist search: {keywords} in {location}")
        
        await rate_limiter.acquire("hirist")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                # Hirist search URL
                search_url = f"https://www.hirist.tech/search/jobs?q={keywords.replace(' ', '+')}&l={location.replace(' ', '+')}"
                
                # Use domcontentloaded then wait
                try:
                    await playwright_manager.navigate(page, search_url, wait_for="domcontentloaded")
                except Exception as e:
                    self.logger.warning(f"Hirist initial navigation failed: {e}. Retrying once...")
                    await page.reload(wait_until="domcontentloaded")
                
                await page.wait_for_timeout(6000)
                
                # Check for empty title or obvious blocks
                title = await page.title()
                if not title or title.strip() == "":
                    self.logger.warning("Hirist: Empty title detected, attempting reload...")
                    await page.reload(wait_until="domcontentloaded")
                    await page.wait_for_timeout(6000)
                
                # Scroll to ensure dynamic content loads
                await page.evaluate("window.scrollBy(0, 1000)")
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        // Hirist v2 uses these specific selectors according to inspection
                        const cards = document.querySelectorAll('a[href*="/j/"], .job-card, [class*="JobCard"]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('[data-testid="job_title"], p.MuiTypography-subtitle2, .job-title');
                                // Company is sometimes in a title attribute of a sibling or specific class
                                const companyEl = card.querySelector('a.MuiTypography-root[title], .company-name, [class*="company"]');
                                const locationEl = card.querySelector('.job-card-location, [class*="location"], .loc-name');
                                const expEl = card.querySelector('.job-card-experience, [class*="exp"], .exp-name');
                                const dateEl = card.querySelector('.job-posted-date, [class*="posted"], .date');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.getAttribute('title') || companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: card.href || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'hirist',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Hirist found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    exp_lower = job.get("experience_required", "").lower()
                    
                    if any(ex.lower() in role_lower for i, ex in enumerate(EXCLUDED_JOB_TITLES)):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                        
                    # Refined Junior-Friendly Filter
                    is_junior_friendly = any(kw in exp_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    has_high_exp = any(kw in exp_lower for kw in ["5", "6", "7", "8", "9", "5+", "8+", "10+"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "lead", "principal", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                        
                    # Also exclude if min exp is already 3+ and no junior match
                    if any(kw in exp_lower for kw in ["3", "4"]) and not is_junior_friendly:
                         # Wait, the user said they WANT "1 to 4" and "2 - 5".
                         # "1 to 4" has "1", so is_junior_friendly is True. Correct.
                         # "2 - 5" has "2", so is_junior_friendly is True. Correct.
                         # "3 - 6" has no 0, 1, 2. is_junior_friendly is False. Correct.
                         pass
                            
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Hirist found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Hirist search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine-learning"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Hirist",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


hirist_agent = HiristAgent()
