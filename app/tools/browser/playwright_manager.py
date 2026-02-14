"""
Playwright Manager - Async browser automation with stealth settings
"""
import sys
import asyncio
import random
import json

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
        self._lock = None

    @property
    def lock(self) -> asyncio.Lock:
        """Lazy lock initialization"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _get_browser(self) -> Browser:
        """Get or create browser instance with lock protection"""
        async with self.lock:
            if self._browser is None or not self._browser.is_connected():
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.settings.headless_browser,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu", # Optimization for cloud
                        "--js-flags=\"--max-old-space-size=256\"", # Target RAM limit
                    ]
                )
                logger.info("Browser launched with memory optimizations")
            return self._browser

    
    async def _get_context(self) -> BrowserContext:
        """Get or create browser context with stealth and resource blocking"""
        if self._context is None:
            browser = await self._get_browser()
            self._context = await browser.new_context(
                viewport={"width": 1280, "height": 720}, # Smaller viewport to save RAM
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                locale="en-US",
                timezone_id="Asia/Kolkata",
            )
            
            # RESOURCE BLOCKING: Skip images, fonts, media to save RAM
            # We now allow stylesheets as some sites use them for critical layout/selector logic
            await self._context.route("**/*", 
                lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

            # Add stealth scripts and more human-like headers
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
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
    
    async def navigate(self, page: Page, url: str, wait_for: str = "domcontentloaded"):
        """Navigate to URL with human-like characteristics"""
        logger.debug(f"Navigating to: {url}")
        try:
            # randomized delay before action
            await asyncio.sleep(random.uniform(1.5, 4.0))
            
            await page.goto(url, wait_until=wait_for, timeout=self.settings.browser_timeout)
            
            # Post-navigation random behaviors
            await self._human_scroll(page)
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise

    async def _human_scroll(self, page: Page):
        """Simulate human reading/scrolling"""
        try:
            # Scroll down a bit
            await page.mouse.wheel(0, random.randint(300, 700))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            # Maybe scroll up a tiny bit
            if random.random() < 0.3:
                await page.mouse.wheel(0, -random.randint(50, 200))
            await asyncio.sleep(random.uniform(0.5, 2.0))
        except:
            pass

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
        """Click element with human-like mouse movement"""
        try:
            element = await page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    # Move mouse to random point within element
                    x = box["x"] + random.uniform(5, box["width"]-5)
                    y = box["y"] + random.uniform(5, box["height"]-5)
                    
                    # Simple human-like curve (steps)
                    await page.mouse.move(x, y, steps=random.randint(5, 15))
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                    await page.mouse.click(x, y)
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            else:
                # Fallback if bounding box fails
                await page.click(selector)
        except Exception as e:
            logger.warning(f"Human click failed for {selector}, using standard click: {e}")
            await page.click(selector)

    async def fill(self, page: Page, selector: str, value: str):
        """Fill input field with human typing simulation"""
        try:
            # Click to focus first
            await self.click(page, selector)
            
            # Type character by character with variable delay
            for char in value:
                await page.keyboard.type(char, delay=random.uniform(30, 120)) # ms
                
                # Occasionally pause
                if random.random() < 0.05:
                    await asyncio.sleep(random.uniform(0.2, 0.8))
            
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.warning(f"Human fill failed, using standard fill: {e}")
            await page.fill(selector, value)

    async def save_storage_state(self, path: str = "state.json"):
        """Save cookies/storage to file"""
        if self._context:
            await self._context.storage_state(path=path)
            logger.info("Session state saved")

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
