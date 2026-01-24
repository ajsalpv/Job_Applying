"""
Playwright Manager - Async browser automation with stealth settings
"""
import sys
import asyncio

# Enforce ProactorEventLoop on Windows for Playwright
if sys.platform == "win32":
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger

logger = get_logger("browser")


class PlaywrightManager:
    """Manage Playwright browser instances with stealth and rate limiting"""
    
    def __init__(self):
        self.settings = get_settings()
        self._browser: Optional[Browser] = None
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()

    
    async def _get_browser(self) -> Browser:
        """Get or create browser instance with lock protection"""
        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.settings.headless_browser,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ]
                )
                logger.info("Browser launched")
            return self._browser

    
    async def _get_context(self) -> BrowserContext:
        """Get or create browser context with stealth settings"""
        if self._context is None:
            browser = await self._get_browser()
            self._context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                locale="en-US",
                timezone_id="Asia/Kolkata",
            )
            
            # Add stealth scripts
            await self._context.add_init_script("""
                // Override webdriver detection
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
        return self._context
    
    @asynccontextmanager
    async def get_page(self):
        """Context manager for getting a new page"""
        context = await self._get_context()
        page = await context.new_page()
        page.set_default_timeout(self.settings.browser_timeout)
        
        try:
            yield page
        finally:
            await page.close()
    
    async def navigate(self, page: Page, url: str, wait_for: str = "networkidle"):
        """Navigate to URL with waiting strategy"""
        logger.debug(f"Navigating to: {url}")
        try:
            await page.goto(url, wait_until=wait_for, timeout=self.settings.browser_timeout)
            # Add random delay to appear human
            await asyncio.sleep(1 + (hash(url) % 3))
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
    
    async def get_page_content(self, page: Page) -> str:
        """Get page HTML content"""
        return await page.content()
    
    async def get_text_content(self, page: Page, selector: str) -> Optional[str]:
        """Get text content of element"""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception as e:
            logger.warning(f"Failed to get text for {selector}: {e}")
        return None
    
    async def get_all_text(self, page: Page, selector: str) -> list:
        """Get text content of all matching elements"""
        try:
            elements = await page.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.text_content()
                if text:
                    texts.append(text.strip())
            return texts
        except Exception as e:
            logger.warning(f"Failed to get texts for {selector}: {e}")
            return []
    
    async def click(self, page: Page, selector: str):
        """Click element with human-like delay"""
        await page.click(selector)
        await asyncio.sleep(0.5)
    
    async def fill(self, page: Page, selector: str, value: str):
        """Fill input field with typing simulation"""
        await page.fill(selector, value)
        await asyncio.sleep(0.3)
    
    async def screenshot(self, page: Page, path: str):
        """Take screenshot for debugging"""
        await page.screenshot(path=path)
        logger.debug(f"Screenshot saved: {path}")
    
    async def close(self):
        """Close browser and cleanup"""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")


# Singleton instance
playwright_manager = PlaywrightManager()
