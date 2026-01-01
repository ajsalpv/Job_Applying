
import asyncio
from app.tools.sheets.sheets_client import sheets_client

def init_headers():
    print("Initializing sheet headers...")
    try:
        # These methods automatically create sheets and headers if missing
        app_sheet = sheets_client.get_applications_sheet()
        print(f"Applications sheet ready: {app_sheet.title}")
        
        fu_sheet = sheets_client.get_followups_sheet()
        print(f"Follow-ups sheet ready: {fu_sheet.title}")
        
    except Exception as e:
        print(f"Failed to initialize sheets: {e}")

if __name__ == "__main__":
    init_headers()
