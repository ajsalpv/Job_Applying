# 💎 TOTAL ENCLOSURE STARTUP
import os, sys, datetime, traceback

def raw_log(msg: str):
    """Raw system write to bypass all buffering"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"\n\xe2\x99\xa6 [{timestamp}] {msg}\n"
        os.write(1, full_msg.encode())
    except:
        pass

raw_log("SYSTEM: Process bootstrap initiated")

# Global Exception Catcher for imports
try:
    raw_log("BOOT: Loading core libraries...")
    raw_log("BOOT: Loading core libraries...")
    import asyncio
    import fastapi
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from contextlib import asynccontextmanager
    
    raw_log("BOOT: Loading internal modules...")
    # We delay orchestrator imports to save RAM
    # from app.api.routes import router
    from app.config.settings import get_settings
    from app.tools.browser import playwright_manager
    from app.tools.utils.logger import get_logger
    from app.orchestrator.scheduler import scheduler
    from app.tools.notifications.telegram_service import telegram_service
    
    raw_log("BOOT: All modules loaded successfully")
except Exception as e:
    raw_log(f"CRITICAL ERROR DURING IMPORT: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)

# Linux Event Loop Stability
if sys.platform != "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        raw_log("BOOT: Event loop policy set for Linux")
    except Exception as e:
        raw_log(f"WARNING: Could not set event loop policy: {e}")

def log_memory():
    """Diagnostic helper to log current RAM usage on Linux/Render"""
    try:
        import os
        with open("/proc/self/status", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "VmRSS" in line:
                    mem = line.split(":")[1].strip()
                    print(f"💎 [RAM] Current Usage: {mem}", flush=True)
                    return mem
    except:
        pass
    return "Unknown"

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Force log flush on startup
    sys.stdout.flush()
    print("💎 [LIFESPAN] Starting...", flush=True)
    log_memory()
    loop = asyncio.get_running_loop()
    logger.info(f"🚀 Starting AI Job Application Agent. Active Event Loop: {type(loop).__name__}")
    log_memory()
    
    if sys.platform == "win32" and not isinstance(loop, asyncio.ProactorEventLoop):
        logger.warning("🚨 REQUIRED ProactorEventLoop is NOT active! Playwright will fail.")

    
    # Start background scheduler
    await scheduler.start()
    
    # Verify required files for Email Bot
    import os
    resume_path = "app/data/Ajsalpv_CV.pdf"
    cl_path = "app/data/cover_letter.txt"
    if os.path.exists(resume_path):
        logger.info(f"✅ Resume found: {resume_path}")
    else:
        logger.error(f"❌ Resume MISSING: {resume_path}")
        
    if os.path.exists(cl_path):
        logger.info(f"✅ Cover letter found: {cl_path}")
    else:
        logger.error(f"❌ Cover letter MISSING: {cl_path}")

    # Verify Gmail API Files
    settings = get_settings()
    
    # Check for Groq Key
    if not settings.groq_api_key:
        logger.error("❌ CRITICAL: GROQ_API_KEY is missing! Bot will crash during job discovery.")
        logger.info("👉 Please add GROQ_API_KEY to your Render Dashboard Environment Variables.")
    else:
        logger.info("✅ GROQ_API_KEY found.")

    if os.path.exists(settings.gmail_credentials_path):
        logger.info(f"✅ Gmail Credentials found: {settings.gmail_credentials_path}")
    else:
        logger.warning(f"⚠️ Gmail Credentials MISSING: {settings.gmail_credentials_path} (Fallback to SMTP)")

    if os.path.exists(settings.gmail_token_path):
        logger.info(f"✅ Gmail Token found: {settings.gmail_token_path}")
    else:
        logger.warning(f"⚠️ Gmail Token MISSING: {settings.gmail_token_path} (Run generate_gmail_token.py locally!)")

    # Start Telegram Listener
    logger.info("🚀 Starting Telegram Listener...")
    asyncio.create_task(telegram_service.start_polling())
    
    # Notify user bot is live (in background to not block startup)
    try:
        from app.tools.notifications.telegram_notifier import notifier
        asyncio.create_task(asyncio.to_thread(
            notifier.send_notification, 
            "🚀 *AI Job Agent is LIVE on Render!*\n\nHealth Check: ✅\nScheduler: ✅\nTelegram Polling: ✅"
        ))
    except Exception as e:
        print(f"⚠️ [LIFESPAN] Failed to send Telegram startup ping: {e}", flush=True)
    
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
    settings = get_settings()
    return {
        "name": "AI Job Application Agent",
        "version": "1.0.0",
        "status": "running",
        "scheduler": {
            "running": scheduler._running,
            "interval": f"{settings.check_interval_minutes} minutes"
        },
        "telegram_polling": telegram_service.running,
        "diagnostics": {
            "gmail_token": os.path.exists(settings.gmail_token_path),
            "groq_key_configured": bool(settings.groq_api_key),
        }
    }


if __name__ == "__main__":
    import uvicorn
    try:
        # Load settings for port
        settings = get_settings()
        port = int(os.environ.get("PORT", 8000))
        raw_log(f"LAUNCH: Starting Uvicorn on port {port}")
        
        # Standard uvicorn run using the loaded app object
        uvicorn.run(
            app,  # Pass the object, not the string, to avoid re-imports
            host="0.0.0.0", 
            port=port, 
            log_level="info",
            access_log=True,
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        raw_log(f"LAUNCH ERROR: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
