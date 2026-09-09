import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
GITHUB_URL = os.getenv("GITHUB_WATCHLIST_URL", "")
GROUP_ID = int(os.getenv("NOTIFICATION_GROUP_ID", 0))
