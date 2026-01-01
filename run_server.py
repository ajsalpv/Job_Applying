import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        # Force ProactorEventLoop for subprocess support (needed for Playwright)
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("🚀 Starting FastAPI Server with ProactorEventLoop...")
    # Disabling reload can help on Windows with loop policies
    # Use loop="asyncio" and explicitly set policy above
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, loop="asyncio")

