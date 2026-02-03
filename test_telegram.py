import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.tools.notifications.telegram_notifier import notifier
from app.config.settings import get_settings

async def test_telegram():
    settings = get_settings()
    print(f"Token present: {bool(settings.telegram_bot_token)}")
    print(f"Chat ID present: {bool(settings.telegram_chat_id)}")
    
    print("Attempting to send test message...")
    success = await notifier.send_notification("🔔 *Test Notification* from Debug Script\nIf you see this, the bot works!")
    
    if success:
        print("✅ Message sent successfully!")
    else:
        print("❌ Failed to send message.")

if __name__ == "__main__":
    asyncio.run(test_telegram())
