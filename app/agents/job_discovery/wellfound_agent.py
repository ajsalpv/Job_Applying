"""
Wellfound (AngelList) Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class WellfoundAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Wellfound job discovery agent for startup roles."""
    
    def __init__(self):
        super().__init__(
            platform="wellfound",
            base_url=PLATFORM_URLS.get(JobPlatform.WELLFOUND, "https://wellfound.com/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "India",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Wellfound-specific job discovery"""
        self.logger.info(f"Wellfound search: {keywords}")
        
        await rate_limiter.acquire("wellfound")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                # Use query-based URL which is often more stable
                search_url = f"https://wellfound.com/jobs?q={keywords.replace(' ', '+')}"
                
                # Navigate and wait for content
                try:
                    await playwright_manager.navigate(page, search_url, wait_for="domcontentloaded")
                except Exception as e:
                    self.logger.warning(f"Wellfound initial navigation failed: {e}. Retrying once...")
                    await page.reload(wait_until="domcontentloaded")
                
                await page.wait_for_timeout(8000) # Wellfound uses heavy JS
                
                # Check for empty title or obvious blocks
                title = await page.title()
                if not title or title.strip() == "":
                    self.logger.warning("Wellfound: Empty title detected, attempting reload...")
                    await page.reload(wait_until="domcontentloaded")
                    await page.wait_for_timeout(6000)
                
                try:
                    await page.wait_for_selector("[data-test='StartupResult'], [class*='styles_component'], .styles_result__, [class*='styles_jobListing']", timeout=15000)
                except:
                    self.logger.warning("Wellfound timeout waiting for job listings. Continuing anyway.")
                
                await page.evaluate("window.scrollBy(0, 500)")
                await page.wait_for_timeout(2000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        // Wellfound uses complex, obfuscated classes
                        const cards = document.querySelectorAll('[data-test="StartupResult"], [class*="styles_component"], [class*="styles_jobListing"], .styles_result__, [class*="JobCard"]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('h4, [class*="jobTitle"], [class*="roleTitle"], [class*="styles_title"]');
                                const companyEl = card.querySelector('h2, [class*="companyName"], [class*="startupName"], [class*="styles_company"]');
                                const locationEl = card.querySelector('[class*="location"], [class*="styles_location"]');
                                const metaEl = card.querySelector('[class*="styles_metadata"], [class*="metadata"]');
                                const linkEl = card.querySelector('a[href*="/jobs/"], a[class*="styles_titleLink"], a[class*="styles_component"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || 'Remote',
                                        experience_required: metaEl?.textContent?.trim() || '0-2 years',
                                        job_url: linkEl?.href || '',
                                        job_description: metaEl?.textContent?.trim() || '',
                                        platform: 'wellfound',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Wellfound found {len(raw_jobs)} raw jobs")
                
                # SMART FALLBACK: If 0 jobs found, use LLM to analyze DOM
                if not raw_jobs:
                    self.logger.warning("Wellfound: 0 jobs found with selectors. Triggering Smart Discovery...")
                    try:
                        from app.agents.job_discovery.smart_discovery import smart_discovery
                        page_content = await page.content()
                        smart_jobs = await smart_discovery.analyze_page(page_content, search_url)
                        if smart_jobs:
                            self.logger.info(f"✨ Smart Discovery salvaged {len(smart_jobs)} jobs!")
                            raw_jobs = smart_jobs
                            for job in raw_jobs:
                                job['platform'] = 'wellfound'
                                job['posted_date'] = job.get('posted_date', 'Today')
                    except Exception as e:
                        self.logger.error(f"Smart Discovery failed: {e}")

                # Standardized intelligent filtering
                from app.config.settings import get_settings
                settings = get_settings()
                target_exp = settings.experience_years

                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    exp_lower = job.get("experience_required", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower:
                        continue
                        
                    # Dynamic Experience Filtering
                    import re
                    exp_nums = re.findall(r'\d+', exp_lower)
                    min_exp = int(exp_nums[0]) if exp_nums else 0
                    
                    if min_exp > (target_exp + 2):
                        continue
                        
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead", "sr.", "manager"]):
                        if target_exp < 5:
                            continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Wellfound found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Wellfound search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "India",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine-learning-engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Wellfound",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


wellfound_agent = WellfoundAgent()
