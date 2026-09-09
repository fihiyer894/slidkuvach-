import asyncio
from datetime import datetime, timedelta
from config import GROUP_ID

LESSONS = [
    {"num": 1, "start": "09:00", "end": "10:20"},
    {"num": 2, "start": "10:40", "end": "12:00"},
    {"num": 3, "start": "12:20", "end": "13:40"},
    {"num": 4, "start": "13:50", "end": "15:10"},
]

def build_schedule_reminders():
    reminders = {}
    for lesson in LESSONS:
        num = lesson["num"]
        start_dt = datetime.strptime(lesson["start"], "%H:%M")
        end_dt = datetime.strptime(lesson["end"], "%H:%M")
        
        for mins in [20, 10, 5]:
            t_start = (start_dt - timedelta(minutes=mins)).strftime("%H:%M")
            msg_start = f"⏰ **До начала {num}-й пары осталось {mins} минут!**\n🕒 Время пары: {lesson['start']} — {lesson['end']}"
            reminders.setdefault(t_start, []).append(msg_start)
            
            t_end = (end_dt - timedelta(minutes=mins)).strftime("%H:%M")
            msg_end = f"⏳ **До конца {num}-й пары осталось {mins} минут!**\n🕒 Конец в {lesson['end']}"
            reminders.setdefault(t_end, []).append(msg_end)
            
    return reminders

async def schedule_loop(bot_client):
    reminders = build_schedule_reminders()
    last_sent_minute = ""

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time != last_sent_minute and current_time in reminders:
            if GROUP_ID != 0:
                for text in reminders[current_time]:
                    try:
                        await bot_client.send_message(chat_id=GROUP_ID, text=text)
                    except Exception as e:
                        print(f"Ошибка отправки расписания в группу: {e}")
            last_sent_minute = current_time

        await asyncio.sleep(15)
