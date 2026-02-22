import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ContentType

# --- НАЛАШТУВАННЯ ---
TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файли
REP_FILE = "reputation.json"
STATS_FILE = "stats.json"
FILTERS_FILE = "filters.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

reputation = load_data(REP_FILE)
stats = load_data(STATS_FILE)
filters = load_data(FILTERS_FILE) # Структура: {"chat_id": {"слово": {"text": "...", "photo": "..."}}}

# --- ФУНКЦІЇ ---

@dp.message(F.new_chat_members)
async def welcome_new_member(message: Message):
    for member in message.new_chat_members:
        text = (
            f"Вітаємо, {member.mention_html()}! 👨‍🌾\n\n"
            f"Ти знайшов свій дім у <b>Hay Day</b> 🌾\n"
            f"Наш чат — найкраще місце для:\n"
            f"📦 Обміну товарами\n"
            f"💡 Порад фермерів\n"
            f"📢 Новин та оновлень\n"
            f"🇺🇦 Мова чату українська!\n\n"
            f"Почни спілкування просто зараз!"
        )
        await message.answer(text, parse_mode="HTML")

@dp.message(Command("filter"))
async def add_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if chat_id not in filters: filters[chat_id] = {}
    
    args = command.args.split(maxsplit=1) if command.args else []
    
    if message.reply_to_message and len(args) >= 1:
        # Варіант 1: відповідь на повідомлення
        trigger = args[0].lower()
        photo_id = message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(args) >= 2:
        # Варіант 2: /filter слово текст
        trigger = args[0].lower()
        text = args[1]
        photo_id = None
    else:
        return await message.answer("Приклад: /filter слово текст (або відповіддю)")

    filters[chat_id][trigger] = {"text": text, "photo": photo_id}
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Збережено фільтр '{trigger}' для цього чату!")

@dp.message(F.text == "+")
async def rep_plus(message: Message):
    if not message.reply_to_message: return
    user = message.reply_to_message.from_user
    uid = str(user.id)
    # Зберігаємо нік та тег для ТОПу
    name = f"{user.full_name} (@{user.username})" if user.username else user.full_name
    
    reputation[uid] = reputation.get(uid, {"score": 0, "name": name})
    reputation[uid]["score"] += 1
    reputation[uid]["name"] = name
    
    save_data(REP_FILE, reputation)
    await message.answer(f"Красава! +1 до карми. Тепер у тебе {reputation[uid]['score']}\n🏆 Твій рівень поваги: {reputation[uid]['score']}")

@dp.message(Command("toprep"))
async def top_rep(message: Message):
    # Сортуємо по score
    sorted_rep = sorted(reputation.items(), key=lambda x: x[1]['score'], reverse=True)[:20]
    msg = "🏆 <b>ТОП-20 репутації чату:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_rep, 1):
        msg += f"{i}. {data['name']} | ID: <code>{uid}</code> — <b>{data['score']}</b>\n"
    await message.answer(msg, parse_mode="HTML")

@dp.message(Command("statistics"))
async def show_stats(message: Message):
    uid = str(message.from_user.id)
    count = stats.get(uid, 0)
    await message.answer(f"📊 Кількість ваших повідомлень: {count}")

@dp.message()
async def global_handler(message: Message):
    uid = str(message.from_user.id)
    chat_id = str(message.chat.id)
    
    # Статистика
    stats[uid] = stats.get(uid, 0) + 1
    save_data(STATS_FILE, stats)

    # Локальні фільтри чату
    if message.text and chat_id in filters:
        word = message.text.lower()
        if word in filters[chat_id]:
            f = filters[chat_id][word]
            if f["photo"]:
                await message.answer_photo(f["photo"], caption=f["text"] or "")
            else:
                await message.answer(f["text"])

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
