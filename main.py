import asyncio
from pyrogram import Client, filters, compose
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from github_sync import watchlist_ids, fetch_watchlist, auto_sync_loop
from schedule_notifier import schedule_loop

userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH)
bot = Client("admin_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@userbot.on_message(filters.group & ~filters.me)
async def monitor_groups(client, message):
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    if user_id in watchlist_ids:
        username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
        full_name = message.from_user.first_name
        if message.from_user.last_name:
            full_name += f" {message.from_user.last_name}"
            
        msg_link = message.link if message.link else "Группа закрытая (нет ссылки)"
        date_str = message.date.strftime("%Y-%m-%d %H:%M:%S")
        
        report = (
            f"🚨 **Обнаружена активность цели!**\n\n"
            f"👤 **Пользователь:** {full_name} ({username})\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"🕒 **Время:** {date_str}\n\n"
            f"💬 **Текст:**\n_{message.text or 'Медиа-сообщение'}_\n\n"
            f"🔗 **Ссылка на сообщение:** {msg_link}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=report)

@bot.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start_cmd(client, message):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("🔄 Обновить базу с GitHub"), KeyboardButton("📊 Анализ")]],
        resize_keyboard=True
    )
    await message.reply("Панель активирована. Бот в дежурном режиме и отслеживает расписание.", reply_markup=keyboard)

@bot.on_message(filters.regex("🔄 Обновить базу с GitHub") & filters.user(ADMIN_ID))
async def manual_sync(client, message):
    success = await fetch_watchlist()
    if success:
        await message.reply(f"✅ База обновлена. В слежке: {len(watchlist_ids)} ID.")
    else:
        await message.reply("❌ Ошибка загрузки с GitHub.")

@bot.on_message(filters.regex("📊 Анализ") & filters.user(ADMIN_ID))
async def analysis_cmd(client, message):
    if not watchlist_ids:
        await message.reply("Список целей пуст.")
        return

    msg = await message.reply("🔄 Собираю данные по целям...")
    report_lines = ["📊 **Отчет Анализа Целей:**\n"]
    
    for uid in watchlist_ids:
        try:
            user = await userbot.get_users(uid)
            uname = f"@{user.username}" if user.username else "Скрыт"
            fname = user.first_name or "Без имени"
            status = "Удален" if user.is_deleted else "Активен"
            
            report_lines.append(
                f"🔹 ID: `{uid}`\n"
                f"👤 Имя: {fname} | Юзернейм: {uname} | Статус: {status}\n"
            )
            await asyncio.sleep(0.5)
        except Exception:
            report_lines.append(f"🔹 ID: `{uid}` - ❌ Ошибка доступа/Не найден\n")
            
    final_report = "\n".join(report_lines)
    
    if len(final_report) > 4000:
        with open("analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(final_report)
        await message.reply_document("analysis_report.txt", caption="Отчет файлом.")
    else:
        await msg.edit_text(final_report)

async def main():
    print("Загрузка базы GitHub...")
    await fetch_watchlist()
    
    asyncio.create_task(auto_sync_loop())
    asyncio.create_task(schedule_loop(bot))
    
    print("Бот и расписание запущены!")
    await compose([userbot, bot])

if __name__ == "__main__":
    asyncio.run(main())
