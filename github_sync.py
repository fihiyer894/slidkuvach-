import aiohttp
import asyncio
from config import GITHUB_URL

watchlist_ids = set()

async def fetch_watchlist():
    global watchlist_ids
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(GITHUB_URL) as response:
                if response.status == 200:
                    text = await response.text()
                    new_ids = {int(line.strip()) for line in text.split('\n') if line.strip().isdigit()}
                    watchlist_ids.update(new_ids)
                    return True
        except Exception as e:
            print(f"Ошибка синхронизации с GitHub: {e}")
    return False

async def auto_sync_loop(interval_seconds=300):
    while True:
        await fetch_watchlist()
        await asyncio.sleep(interval_seconds)
