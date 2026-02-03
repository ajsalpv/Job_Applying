"""
Telegram Notifier - Send mobile notifications
"""
import asyncio
import requests
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger
from app.tools.utils.retry import telegram_retry

logger = get_logger("telegram")

class TelegramNotifier:
    """Send notifications via Telegram Bot"""
    
    def __init__(self):
        self.settings = get_settings()
        self.token = self.settings.telegram_bot_token
        self.chat_id = self.settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
    @telegram_retry
    async def send_notification(self, message: str) -> bool:
        """
        Send a text message notification asynchronously
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            # Wrap blocking requests in a thread
            def do_send():
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                return True

            await asyncio.to_thread(do_send)
            logger.info("Notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

# Global instance
notifier = TelegramNotifier()
