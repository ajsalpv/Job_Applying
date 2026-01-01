"""
App package initialization
"""
import sys
import asyncio

# Enforce ProactorEventLoop on Windows for Playwright and subprocesses
if sys.platform == "win32":
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

__all__ = []

