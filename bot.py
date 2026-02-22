import json
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

# --- НАЛАШТУВАННЯ ---
TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файли для збереження даних (вимога від 22.02.2026)
REP_FILE = "reputation_history.json"
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

# Завантажуємо дані при старті
rep_data = load_data(REP_FILE) 
# Структура: {"uid": {"name": "Ім'я", "history": ["2026-02-22", "2026-02-22"]}}
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
    if target.id == message.from_user.id: return # Самому собі не можна
    
    uid = str(target.id)
    today = datetime.now().strftime("%Y-%m-%d")
    name = target.full_name

    if uid not in rep_data:
        rep_data[uid] = {"name": name, "history": []}
    
    rep_data[uid]["history"].append(today)
    rep_data[uid]["name"] = name # Оновлюємо ім'я
    save_data(REP_FILE, rep_data)
    
    await message.answer(f"👍 {name} отримав +1 до репутації! (Всього: {len(rep_data[uid]['history'])})")

# --- ТОП ЗА ВЕСЬ ЧАС ---
@dp.message(Command("toprep"))
async def top_total(message: Message):
    items = []
    for uid, data in rep_data.items():
        items.append((data["name"], len(data["history"])))
    
    items.sort(key=lambda x: x[1], reverse=True)
    msg = "🏆 <b>ТОП-20 репутації за весь час:</b>\n\n"
    for i, (name, score) in enumerate(items[:20], 1):
        msg += f"{i}. {name} — <b>{score}</b>\n"
    await message.answer(msg, parse_mode="HTML")

# --- ТОП ЗА ПЕРІОД (/toprepm 2026.01.01 2026.02.21) ---
@dp.message(Command("toprepm"))
async def top_period(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer("Використовуй: <code>/toprepm 2026.01.01 2026.02.21</code>", parse_mode="HTML")
    
    try:
        args = command.args.replace(".", "-").split()
        start_dt = datetime.strptime(args[0], "%Y-%m-%d")
        end_dt = datetime.strptime(args[1], "%Y-%m-%d")
    except:
        return await message.answer("Помилка формату! Треба: РРРР.ММ.ДД")

    period_results = []
    for uid, data in rep_data.items():
        count = 0
        for d_str in data["history"]:
            curr_d = datetime.strptime(d_str, "%Y-%m-%d")
            if start_dt <= curr_d <= end_dt:
                count += 1
        if count > 0:
            period_results.append((data["name"], count))

    period_results.sort(key=lambda x: x[1], reverse=True)
    
    msg = f"📊 <b>ТОП-20 за період {args[0]} — {args[1]}:</b>\n\n"
    if not period_results:
        msg += "За цей період ніхто не отримував репутацію."
    else:
        for i, (name, score) in enumerate(period_results[:20], 1):
            msg += f"{i}. {name} — <b>{score}</b>\n"
    
    await message.answer(msg, parse_mode="HTML")

# --- ФІЛЬТРИ ---
@dp.message(Command("filter"))
async def set_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if chat_id not in filters: filters[chat_id] = {}
    
    if not message.reply_to_message or not command.args:
        return await message.answer("Відповідай на повідомлення командою: <code>/filter слово</code>", parse_mode="HTML")
    
    trigger = command.args.lower()
    rep = message.reply_to_message
    
    filters[chat_id][trigger] = {
        "text": rep.text or rep.caption,
        "photo": rep.photo[-1].file_id if rep.photo else None
    }
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр на слово '{trigger}' збережено!")

@dp.message()
async def handle_all(message: Message):
    if not message.text: return
    cid = str(message.chat.id)
    word = message.text.lower()
    
    if cid in filters and word in filters[cid]:
        f = filters[cid][word]
        if f["photo"]: await message.answer_photo(f["photo"], caption=f["text"] or "")
        else: await message.answer(f["text"])

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
