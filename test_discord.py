import os
import requests
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.environ.get("DISCORD_WEBHOOK")

message = {
    "content": "🚨 **AIOps Alert Test:** Cluster is being monitored...... No errors found! 🚀"
}

response = requests.post(webhook_url, json=message)
print(f"Status Code: {response.status_code}")
