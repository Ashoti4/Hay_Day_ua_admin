import json
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hlink

# --- НАЛАШТУВАННЯ ---
TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файли збереження (вимога від 22.02.2026)
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

# Структура: {"uid": {"name": "...", "rep_history": [...], "msg_history": [...]}}
db = load_data(DATA_FILE)
filters = load_data(FILTERS_FILE)

# --- ПРИВІТАННЯ ---
@dp.message(F.new_chat_members)
async def welcome(message: Message):
    for member in message.new_chat_members:
        text = (
            f"Вітаємо, {member.mention_html()}! 🍎\n\n"
            f"Ти знайшов свій дім у <b>Hay Day</b> ✨\n"
            f"Наш чат — найкраще місце для:\n"
            f"📦 Обміну товарами (забудь про дефіцит!)\n"
            f"💡 Порад від досвідчених фермерів\n"
            f"📢 Новин про події та оновлення\n"
            f"🇺🇦 Мова чату українська!\n\n"
            f"Почни спілкування просто зараз!"
        )
        await message.answer(text, parse_mode="HTML")

# --- РЕПУТАЦІЯ ("+") ---
@dp.message(F.text == "+")
async def add_rep(message: Message):
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id: return
    
    uid = str(target.id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in db: db[uid] = {"name": target.full_name, "rep_history": [], "msg_history": []}
    db[uid]["rep_history"].append(today)
    db[uid]["name"] = target.full_name
    save_data(DATA_FILE, db)
    
    await message.answer(f"👍 {hlink(target.full_name, f'tg://user?id={target.id}')} отримав +1 до репутації!", parse_mode="HTML")

# --- СТАТИСТИКА ПОВІДОМЛЕНЬ ---
@dp.message(Command("statistics"))
async def stats_total(message: Message):
    items = []
    for uid, data in db.items():
        items.append((data["name"], uid, len(data.get("msg_history", []))))
    
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "📊 <b>Статистика повідомлень за весь час:</b>\n\n"
    for i, (name, uid, count) in enumerate(items[:20], 1):
        msg += f"{i}. {hlink(name, f'tg://user?id={uid}')} — <b>{count}</b>\n"
    await message.answer(msg, parse_mode="HTML")

@dp.message(Command("statisticsm"))
async def stats_period(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer("Формат: <code>/statisticsm 2026.01.01 2026.02.22</code>", parse_mode="HTML")
    
    try:
        args = command.args.replace(".", "-").split()
        start_dt = datetime.strptime(args[0], "%Y-%m-%d")
        end_dt = datetime.strptime(args[1], "%Y-%m-%d")
    except: return await message.answer("Помилка формату!")

    res = []
    for uid, data in db.items():
        count = sum(1 for d in data.get("msg_history", []) if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt)
        if count > 0: res.append((data["name"], uid, count))

    res.sort(key=lambda x: x[2], reverse=True)
    msg = f"🗓 <b>Повідомлення за період {args[0]} — {args[1]}:</b>\n\n"
    for i, (name, uid, count) in enumerate(res[:20], 1):
        msg += f"{i}. {hlink(name, f'tg://user?id={uid}')} — <b>{count}</b>\n"
    await message.answer(msg if res else "Немає даних за цей період.", parse_mode="HTML")

# --- ТОПИ РЕПУТАЦІЇ ---
@dp.message(Command("toprep"))
async def top_total(message: Message):
    items = []
    for uid, data in db.items():
        items.append((data["name"], uid, len(data.get("rep_history", []))))
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "🏆 <b>ТОП-20 репутації за весь час:</b>\n\n"
    for i, (name, uid, score) in enumerate(items[:20], 1):
        msg += f"{i}. {hlink(name, f'tg://user?id={uid}')} — <b>{score}</b>\n"
    await message.answer(msg, parse_mode="HTML")

@dp.message(Command("toprepm"))
async def top_period(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer("Формат: <code>/toprepm 2026.01.01 2026.02.22</code>", parse_mode="HTML")
    args = command.args.replace(".", "-").split()
    start_dt = datetime.strptime(args[0], "%Y-%m-%d")
    end_dt = datetime.strptime(args[1], "%Y-%m-%d")

    res = []
    for uid, data in db.items():
        count = sum(1 for d in data.get("rep_history", []) if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt)
        if count > 0: res.append((data["name"], uid, count))
    res.sort(key=lambda x: x[2], reverse=True)
    
    msg = f"📊 <b>ТОП репутації за період {args[0]} — {args[1]}:</b>\n\n"
    for i, (name, uid, score) in enumerate(res[:20], 1):
        msg += f"{i}. {hlink(name, f'tg://user?id={uid}')} — <b>{score}</b>\n"
    await message.answer(msg if res else "Ніхто не отримував репутацію.", parse_mode="HTML")

# --- ФІЛЬТРИ ---
@dp.message(Command("filter"))
async def filter_cmd(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if not command.args:
        if chat_id not in filters or not filters[chat_id]: return await message.answer("Список фільтрів порожній.")
        list_f = "\n".join([f"- {word}" for word in filters[chat_id].keys()])
        return await message.answer(f"✅ <b>Активні фільтри:</b>\n{list_f}", parse_mode="HTML")
    
    if not message.reply_to_message: return await message.answer("Відповідай на повідомлення командою <code>/filter слово</code>")
    trigger = command.args.lower()
    if chat_id not in filters: filters[chat_id] = {}
    filters[chat_id][trigger] = {"text": message.reply_to_message.text or message.reply_to_message.caption, "photo": message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None}
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр '<b>{trigger}</b>' збережено!", parse_mode="HTML")

# --- ЗАГАЛЬНИЙ ХЕНДЛЕР (СТАТИСТИКА ТА ФІЛЬТРИ) ---
@dp.message()
async def handle_all(message: Message):
    if not message.from_user or message.from_user.is_bot: return
    uid = str(message.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    # Логування повідомлення для статистики
    if uid not in db: db[uid] = {"name": message.from_user.full_name, "rep_history": [], "msg_history": []}
    db[uid]["msg_history"].append(today)
    db[uid]["name"] = message.from_user.full_name
    save_data(DATA_FILE, db)

    # Перевірка фільтрів
    if message.text:
        cid = str(message.chat.id)
        word = message.text.lower()
        if cid in filters and word in filters[cid]:
            f = filters[cid][word]
            if f["photo"]: await message.answer_photo(f["photo"], caption=f["text"] or "")
            else: await message.answer(f["text"])

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
