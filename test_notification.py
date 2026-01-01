
from app.tools.notifications.telegram_notifier import notifier

print("Sending test notification...")
success = notifier.send_notification("🔔 *Test Notification*\nThis is a test from your Job Application Agent.")

if success:
    print("✅ Notification sent successfully!")
else:
    print("❌ Failed to send notification.")
