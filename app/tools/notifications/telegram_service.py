import asyncio
import re
from typing import Optional
import requests
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger
from app.tools.utils.email_sender import email_sender

logger = get_logger("telegram_service")

class TelegramService:
    """
    Background service to poll Telegram for user commands.
    Supported Commands:
    - <email> <position>: Send application email
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.token = self.settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = False
        self.last_update_id = 0
        
    async def start_polling(self):
        """Start long-polling loop"""
        if not self.token:
            logger.warning("Telegram token missing. Polling service disabled.")
            return

        self.running = True
        logger.info("🤖 Telegram Bot Polling Started...")
        
        while self.running:
            try:
                updates = await self._get_updates()
                for update in updates:
                    await self._process_update(update)
                    self.last_update_id = update["update_id"] + 1
                    
                await asyncio.sleep(1) # Prevent tight loop
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
                
    def stop(self):
        """Stop polling"""
        self.running = False
        logger.info("Telegram Bot Polling Stopped")

    async def _get_updates(self):
        """Fetch updates from Telegram API"""
        params = {"offset": self.last_update_id, "timeout": 30}
        try:
            # Wrap blocking requests in a thread to keep event loop alive
            def fetch():
                return requests.get(f"{self.base_url}/getUpdates", params=params, timeout=40)
            
            response = await asyncio.to_thread(fetch)
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            return []
        except Exception:
            return []

    async def _process_update(self, update: dict):
        """Process a single update"""
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")
        
        if not text or not chat_id:
            return
            
        # Verify it's the authorized user
        if str(chat_id) != str(self.settings.telegram_chat_id):
            return 
            
        logger.info(f"Received Telegram command: {text}")
        
        # Regex for Email Command: <email> <position>
        # e.g. "recruiter@gmail.com AI Engineer"
        # Handles simple email extraction
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        email_match = re.search(email_pattern, text)
        
        if email_match:
            email = email_match.group(0)
            # Position is everything else
            position = text.replace(email, "").strip()
            # Clean up extra chars if they typed "email: ..."
            position = position.replace(":", "").strip()
            
            if not position:
                self._send_message(chat_id, "❌ Please specify a position name. Format: `<email> <position>`")
                return

            self._send_message(chat_id, f"⏳ Sending application to *{email}* for *{position}*...")
            
            # Send using EmailSender in a background thread to avoid blocking polling
            def sync_send():
                return email_sender.send_application(
                    to_email=email,
                    position_name=position
                )
            
            success, result_message = await asyncio.to_thread(sync_send)
            
            if success:
                self._send_message(chat_id, f"✅ Application Sent Successfully!\n\n📧 To: {email}\n💼 Role: {position}")
            else:
                self._send_message(chat_id, f"❌ Failed to send email:\n`{result_message}`")
        else:
            # Ignore other messages or provide help
            if text == "/help" or text == "/start":
                self._send_message(chat_id, "Commands:\n`email@example.com Position Name` - Send Application")

    async def _send_message_async(self, chat_id, text):
        """Reply to user asynchronously"""
        def send():
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                requests.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send Telegram reply: {e}")
        
        await asyncio.to_thread(send)

    def _send_message(self, chat_id, text):
        """Old sync method (kept for internal use but better use async)"""
        try:
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            requests.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send Telegram reply: {e}")

telegram_service = TelegramService()
