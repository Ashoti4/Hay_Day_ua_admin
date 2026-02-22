import json
import os
import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hlink

# --- НАЛАШТУВАННЯ ---
TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "bot_data.json"
FILTERS_FILE = "filters.json"

def load_data(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data(DATA_FILE)
filters = load_data(FILTERS_FILE)

def get_user_link(uid, name):
    return hlink(name, f"tg://user?id={uid}")

# --- ПРИВІТАННЯ З ОФОРМЛЕННЯМ ТА НІКОМ ---
@dp.message(F.new_chat_members)
async def welcome(message: Message):
    # Отримуємо нік людини
    user_name = message.new_chat_members[0].mention_html()
    
    # Твої варіанти з ніком на початку та смайликами
    greetings = [
        f"{user_name} 👋 <b>Ласкаво просимо в HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞</b>\n\nТут обговорюють і Hay Day, і життя, і все між цим 😏\nПочувайся як вдома, але не забувай: ферма сама себе не прокачає 🚜🌾",
        
        f"{user_name} 🍅 <b>Новий фермер у курилці! 🐷💨</b>\n\nЗаходь, розкладай помідори по ящиках і знайомся з нашими неадекватами 😂🔥\nТут можна: питати про гру, жалітись на події і просто базікати про життя 🍻🍎",
        
        f"{user_name} 🚬 <b>Вітаємо в нашому борделі… ой, курилці 💃🥒</b>\n\nТут дорослі розмови, дружня атмосфера і Hay Day без пафосу ✨🚜\nЯкщо загубишся — питай, не кусаємось (ну майже) 😉🍓",
        
        f"{user_name} 🚜 <b>Ти щойно заїхав(ла) у HAY DAY ua БОРДЕЛЬ-КУРІЛКА 🌽💨</b>\n\nТут можна:\n🔹 скиглити на Грега 🎅😒\n🔹 хизуватись фермами 🏗💎\n🔹 просто поговорити про життя 🗣🍺\n\nРозташовуйся зручно! ✨🍏",
        
        f"{user_name} 👋 <b>Ласкаво просимо в HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞</b>\n\nТут без цензури, зате з гумором і підтримкою 😉\nПочувайся як вдома. Якщо потрібна допомога — питай, ми не кусаємось (ну, майже) 🚜🌾"
    ]
    
    await message.answer(random.choice(greetings), parse_mode="HTML")

# --- РЕПУТАЦІЯ ---
@dp.message(F.text == "+")
async def add_rep(message: Message):
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id or target.is_bot: return
    
    uid = str(target.id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in db: db[uid] = {"name": target.full_name, "rep_history": [], "msg_history": []}
    db[uid]["rep_history"].append(today)
    db[uid]["name"] = target.full_name
    save_data(DATA_FILE, db)
    
    await message.answer(f"👍 {get_user_link(uid, target.full_name)} отримав +1 до репутації!", parse_mode="HTML")

# --- КОМАНДА /filters (СПИСОК) ---
@dp.message(Command("filters"))
async def show_filters(message: Message):
    chat_id = str(message.chat.id)
    if chat_id not in filters or not filters[chat_id]:
        return await message.answer("Список фільтрів порожній.")
    
    list_f = "\n".join([f"- <code>{word}</code>" for word in filters[chat_id].keys()])
    header = "<b>Список фільтрів у HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞:</b>\n"
    await message.answer(f"{header}{list_f}", parse_mode="HTML")

# --- КОМАНДА /filter (ДОДАТИ) ---
@dp.message(Command("filter"))
async def set_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if not command.args or not message.reply_to_message:
        return await message.answer("Відповідай на повідомлення командою <code>/filter слово</code>")
    
    trigger = command.args.lower()
    if chat_id not in filters: filters[chat_id] = {}
    
    filters[chat_id][trigger] = {
        "text": message.reply_to_message.text or message.reply_to_message.caption,
        "photo": message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None
    }
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр '<b>{trigger}</b>' збережено!", parse_mode="HTML")

# --- КОМАНДА /stop (ВИДАЛИТИ) ---
@dp.message(Command("stop"))
async def stop_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if not command.args: return await message.answer("Вкажи слово: <code>/stop слово</code>")
    trigger = command.args.lower()
    if chat_id in filters and trigger in filters[chat_id]:
        del filters[chat_id][trigger]
        save_data(FILTERS_FILE, filters)
        await message.answer(f"🚫 Фільтр '<b>{trigger}</b>' видалено.", parse_mode="HTML")
    else: await message.answer("Фільтр не знайдено.")

# --- СТАТИСТИКА ПОВІДОМЛЕНЬ ---
@dp.message(Command("statistics"))
async def stats_total(message: Message):
    items = [(data["name"], uid, len(data.get("msg_history", []))) for uid, data in db.items() if len(data.get("msg_history", [])) > 0]
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "📊 <b>Статистика повідомлень за весь час:</b>\n\n"
    for i, (name, uid, count) in enumerate(items[:20], 1):
        msg += f"{i}. {get_user_link(uid, name)} — <b>{count}</b>\n"
    await message.answer(msg if items else "Статистика порожня.", parse_mode="HTML")

# --- ОБРОБКА ПОВІДОМЛЕНЬ ---
@dp.message()
async def handle_all(message: Message):
    if not message.from_user or message.from_user.is_bot: return
    uid, today = str(message.from_user.id), datetime.now().strftime("%Y-%m-%d")
    
    if uid not in db: db[uid] = {"name": message.from_user.full_name, "rep_history": [], "msg_history": []}
    db[uid]["msg_history"].append(today)
    db[uid]["name"] = message.from_user.full_name
    save_data(DATA_FILE, db)

    if message.text:
        cid, word = str(message.chat.id), message.text.lower()
        if cid in filters and word in filters[cid]:
            f = filters[cid][word]
            if f.get("photo"): await message.answer_photo(f["photo"], caption=f["text"] or "")
            else: await message.answer(f["text"])

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
