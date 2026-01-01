
import requests
import json

token = "8380477714:AAEB790RVdawDIzOWupFl191cbIJ7dH1yqo"
url = f"https://api.telegram.org/bot{token}/getUpdates"

try:
    response = requests.get(url)
    data = response.json()
    
    if data.get("ok") and data.get("result"):
        # Get the first result's message chat id
        chat_id = data["result"][0]["message"]["chat"]["id"]
        print(f"CHAT_ID_FOUND: {chat_id}")
    else:
        print("NO_UPDATES_FOUND")
        print(json.dumps(data, indent=2))
        
except Exception as e:
    print(f"ERROR: {e}")
