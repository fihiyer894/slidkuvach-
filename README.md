# Telegram Bot: Слежка + Расписание пар

## Быстрый старт:
1. Распакуйте архив в отдельную папку.
2. Переименуйте `.env.example` в `.env` и заполните:
   - `BOT_TOKEN` — токен бота от @BotFather.
   - `ADMIN_ID` — ваш Telegram ID (от @userinfobot).
   - `GROUP_ID` — ID группы с минусом (от @myidbot).
3. Заполните `users.txt` — впишите ID пользователей для слежки (по одному на строку).
4. Установите зависимости: `pip install -r requirements.txt`
5. Запустите бота: `python main.py`

⚠️ **Важно:** Чтобы бот видел все сообщения в группе, сделайте его администратором группы или выключите Group Privacy у @BotFather (`/mybots` -> выбор бота -> *Bot Settings* -> *Group Privacy* -> *Turn off*).
