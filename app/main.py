"""
Main FastAPI Application Entry Point
"""
import sys
import asyncio

# Enforce ProactorEventLoop on Windows for Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.config.settings import get_settings
from app.tools.browser import playwright_manager
from app.tools.utils.logger import get_logger
from app.orchestrator.scheduler import scheduler
from app.tools.notifications.telegram_service import telegram_service

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    loop = asyncio.get_running_loop()
    logger.info(f"🚀 Starting AI Job Application Agent. Active Event Loop: {type(loop).__name__}")
    
    if sys.platform == "win32" and not isinstance(loop, asyncio.ProactorEventLoop):
        logger.warning("🚨 REQUIRED ProactorEventLoop is NOT active! Playwright will fail.")

    
    # Start background scheduler
    await scheduler.start()
    
    # Start Telegram Listener
    asyncio.create_task(telegram_service.start_polling())
    
    yield
    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")
    await scheduler.stop()
    telegram_service.stop()
    await playwright_manager.close()


app = FastAPI(
    title="AI Job Application Agent",
    description="AI-powered job discovery, scoring, and application assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["Jobs"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Job Application Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
