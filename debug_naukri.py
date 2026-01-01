
import asyncio
from playwright.async_api import async_playwright

async def debug_naukri():
    async with async_playwright() as p:
        # Launch headed to avoid some detection, but headless=True is default in app
        # We try headless first as in app
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        url = "https://www.naukri.com/ai-engineer-jobs-in-bangalore?experience=1-3"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)
            
            print("Taking screenshot...")
            await page.screenshot(path="naukri_debug.png")
            
            content = await page.content()
            with open("naukri.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("Done. Check naukri_debug.png and naukri.html")
            
            # Print title
            title = await page.title()
            print(f"Page Title: {title}")
            
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="naukri_error.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_naukri())
