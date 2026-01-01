
import sys
import os

print("Checking imports...")

try:
    print("1. Importing settings...")
    from app.config.settings import get_settings
    
    print("2. Importing constants...")
    from app.config.constants import JobPlatform
    
    print("3. Importing tools...")
    from app.tools.utils.logger import get_logger
    from app.tools.notifications.telegram_notifier import notifier
    
    print("4. Importing agents...")
    from app.agents.tracking.tracking_agent import tracking_agent
    
    print("5. Importing orchestrator...")
    from app.orchestrator.orchestrator import create_workflow, run_discovery_phase
    
    print("6. Importing main app...")
    # Be careful not to start the server, just import
    from app.main import app
    
    print("✅ All modules imported successfully!")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
