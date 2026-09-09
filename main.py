import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
GROUP_ID = int(os.getenv("GROUP_ID", 0))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = "/webhook"

# Render автоматически передает порт в переменную PORT
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Чтение локального файла users.txt ---
USERS_FILE = "users.txt"

def load_watchlist() -> set:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    return set()

watchlist_ids = load_watchlist()

# --- Расписание пар ---
LESSONS = [
    {"num": 1, "start": "09:00", "end": "10:20"},
    {"num": 2, "start": "10:40", "end": "12:00"},
    {"num": 3, "start": "12:20", "end": "13:40"},
    {"num": 4, "start": "13:50", "end": "15:10"},
]

def build_reminders():
    reminders = {}
    for lesson in LESSONS:
        num = lesson["num"]
        start_dt = datetime.strptime(lesson["start"], "%H:%M")
        end_dt = datetime.strptime(lesson["end"], "%H:%M")
        
        for mins in [20, 10, 5]:
            t_start = (start_dt - timedelta(minutes=mins)).strftime("%H:%M")
            msg_start = f"⏰ **До начала {num}-й пары осталось {mins} минут!**\n🕒 Время: {lesson['start']} — {lesson['end']}"
            reminders.setdefault(t_start, []).append(msg_start)
            
            t_end = (end_dt - timedelta(minutes=mins)).strftime("%H:%M")
            msg_end = f"⏳ **До конца {num}-й пары осталось {mins} минут!**\n🕒 Конец в {lesson['end']}"
            reminders.setdefault(t_end, []).append(msg_end)
            
    return reminders

async def schedule_loop():
    reminders = build_reminders()
    last_sent_minute = ""

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time != last_sent_minute and current_time in reminders:
            if GROUP_ID != 0:
                for text in reminders[current_time]:
                    try:
                        await bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Ошибка отправки напоминания: {e}")
            last_sent_minute = current_time

        await asyncio.sleep(15)

# --- Перехват сообщений в группе ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def monitor_messages(message: types.Message):
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    if user_id in watchlist_ids:
        username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
        full_name = message.from_user.full_name
        
        if message.chat.username:
            msg_link = f"https://t.me/{message.chat.username}/{message.message_id}"
        else:
            chat_id_str = str(message.chat.id).replace("-100", "")
            msg_link = f"https://t.me/c/{chat_id_str}/{message.message_id}"

        date_str = message.date.strftime("%Y-%m-%d %H:%M:%S")
        
        report = (
            f"🚨 **Обнаружена активность цели!**\n\n"
            f"👤 **Пользователь:** {full_name} ({username})\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"🕒 **Время:** {date_str}\n\n"
            f"💬 **Текст:**\n_{message.text or message.caption or 'Медиа/Файл'}_\n\n"
            f"🔗 **Ссылка:** {msg_link}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="Markdown")

# --- Управление для Админа ---
@dp.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def start_cmd(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔄 Обновить users.txt"), KeyboardButton(text="📊 Анализ")]],
        resize_keyboard=True
    )
    await message.reply("Панель активирована. Бот работает через Webhook.", reply_markup=keyboard)

@dp.message(F.text == "🔄 Обновить users.txt", F.from_user.id == ADMIN_ID)
async def manual_sync(message: types.Message):
    global watchlist_ids
    watchlist_ids = load_watchlist()
    await message.reply(f"✅ Файл перечитан. В слежке: {len(watchlist_ids)} ID.")

@dp.message(F.text == "📊 Анализ", F.from_user.id == ADMIN_ID)
async def analysis_cmd(message: types.Message):
    if not watchlist_ids:
        await message.reply("Список users.txt пуст.")
        return

    msg = await message.reply("🔄 Проверяю участников...")
    report_lines = ["📊 **Отчет Анализа Целей:**\n"]
    
    for uid in watchlist_ids:
        try:
            member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=uid)
            user = member.user
            uname = f"@{user.username}" if user.username else "Скрыт"
            fname = user.full_name
            status = member.status
            
            report_lines.append(f"🔹 ID: `{uid}` | {fname} ({uname})\n  Статус в группе: `{status}`\n")
        except Exception:
            report_lines.append(f"🔹 ID: `{uid}` — не найден в группе\n")
        await asyncio.sleep(0.2)
            
    final_report = "\n".join(report_lines)
    
    if len(final_report) > 4000:
        with open("analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(final_report)
        await message.reply_document(FSInputFile("analysis_report.txt"), caption="Отчет файлом.")
    else:
        await msg.edit_text(final_report, parse_mode="Markdown")

# --- Настройка Webhook и Web-сервера ---
async def on_startup(bot: Bot):
    webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    asyncio.create_task(schedule_loop())

async def health_check(request):
    return web.Response(text="Bot is running!")

def main():
    dp.startup.register(on_startup)
    
    app = web.Application()
    app.router.add_get("/", health_check)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
