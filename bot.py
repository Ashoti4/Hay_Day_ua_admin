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
CHAT_LINK = "https://t.me/hayday18pluS"
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

def get_footer():
    return f"\n\n🏠 {hlink('@hayday18pluS', CHAT_LINK)}"

async def is_admin(message: Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ('administrator', 'creator')

# --- ПРИВІТАННЯ ТА ПРОЩАННЯ ---
@dp.message(F.new_chat_members)
async def welcome(message: Message):
    for member in message.new_chat_members:
        user_name = member.mention_html()
        welcome_text = (
            f"{user_name}, 👋 ласкаво просимо в HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞\n\n"
            f"Тут без цензури, зате з гумором і підтримкою 😉\n"
            f"Почувайся як вдома. Якщо потрібна допомога — питай!"
        )
        await message.answer(f"{welcome_text}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.left_chat_member)
async def goodbye(message: Message):
    user_name = message.left_chat_member.full_name
    # Твій персоналізований текст прощання
    bye_text = f"🌬 {user_name} втік(ла) з ферми... Певно, коза в дупу боднула"
    await message.answer(f"{bye_text}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

# --- РЕПУТАЦІЯ ОКРЕМО ДЛЯ КОЖНОГО ЧАТУ ---
@dp.message(F.text.in_({"+", "-"}))
async def change_rep(message: Message):
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id or target.is_bot: return
    
    cid, uid = str(message.chat.id), str(target.id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if cid not in db: db[cid] = {}
    if uid not in db[cid]: 
        db[cid][uid] = {"name": target.full_name, "rep_history": [], "msg_history": []}
    
    if message.text == "+":
        db[cid][uid].setdefault("rep_history", []).append(today)
        act, emo = "отримав +1 до репутації!", "👍"
    else:
        history = db[cid][uid].get("rep_history", [])
        if history: history.pop()
        act, emo = "втратив -1 від репутації!", "👎"
    
    db[cid][uid]["name"] = target.full_name
    save_data(DATA_FILE, db)
    
    total = len(db[cid][uid].get("rep_history", []))
    resp = f"{emo} {get_user_link(uid, target.full_name)} {act}\nТвоя репутація тут: <b>{total}</b>"
    await message.answer(f"{resp}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

# --- ТОПИ ТА СТАТИСТИКА ---
@dp.message(Command("toprep"))
async def top_total(message: Message):
    cid = str(message.chat.id)
    if cid not in db: return await message.answer(f"Даних немає.{get_footer()}", parse_mode="HTML")
    items = [(d["name"], u, len(d.get("rep_history", []))) for u, d in db[cid].items() if d.get("rep_history")]
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "🏆 <b>ТОП-20 репутації чату:</b>\n\n"
    for i, (n, u, s) in enumerate(items[:20], 1): msg += f"{i}. {get_user_link(u, n)} — <b>{s}</b>\n"
    await message.answer(f"{msg if items else 'ТОП порожній.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("toprepm"))
async def top_period(message: Message, command: CommandObject):
    cid = str(message.chat.id)
    if not command.args or len(command.args.split()) < 2 or cid not in db:
        return await message.answer(f"Формат: <code>/toprepm 2026.01.01 2026.12.31</code>{get_footer()}", parse_mode="HTML")
    try:
        args = command.args.replace(".", "-").split()
        s_dt, e_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res = []
        for u, d in db[cid].items():
            cnt = sum(1 for x in d.get("rep_history", []) if s_dt <= datetime.strptime(x, "%Y-%m-%d") <= e_dt)
            if cnt > 0: res.append((d["name"], u, cnt))
        res.sort(key=lambda x: x[2], reverse=True)
        msg = f"🗓 <b>ТОП репутації ({args[0]} - {args[1]}):</b>\n\n"
        for i, (n, u, s) in enumerate(res[:20], 1): msg += f"{i}. {get_user_link(u, n)} — <b>{s}</b>\n"
        await message.answer(f"{msg if res else 'Даних немає.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)
    except: await message.answer("Помилка формату дат!")

@dp.message(Command("statisticsm"))
async def stats_period(message: Message, command: CommandObject):
    cid = str(message.chat.id)
    if not command.args or len(command.args.split()) < 2 or cid not in db:
        return await message.answer(f"Формат: <code>/statisticsm 2026.01.01 2026.12.31</code>{get_footer()}", parse_mode="HTML")
    try:
        args = command.args.replace(".", "-").split()
        s_dt, e_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res = []
        for u, d in db[cid].items():
            cnt = sum(1 for x in d.get("msg_history", []) if s_dt <= datetime.strptime(x, "%Y-%m-%d") <= e_dt)
            if cnt > 0: res.append((d["name"], u, cnt))
        res.sort(key=lambda x: x[2], reverse=True)
        msg = f"🗓 <b>Статистика повідомлень ({args[0]} - {args[1]}):</b>\n\n"
        for i, (n, u, s) in enumerate(res[:20], 1): msg += f"{i}. {get_user_link(u, n)} — <b>{s}</b>\n"
        await message.answer(f"{msg if res else 'Даних немає.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)
    except: await message.answer("Помилка формату дат!")

# --- ФІЛЬТРИ ---
@dp.message(Command("filter"))
async def set_filter(message: Message, command: CommandObject):
    if not await is_admin(message): return
    if not command.args or not message.reply_to_message: return await message.answer("Відповідай на повідомлення: /filter слово")
    cid, trigger = str(message.chat.id), command.args.lower()
    if cid not in filters: filters[cid] = {}
    filters[cid][trigger] = {"text": message.reply_to_message.text or message.reply_to_message.caption,
                             "photo": message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None}
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр '<b>{trigger}</b>' збережено!", parse_mode="HTML")

# --- ОБРОБНИК ---
@dp.message()
async def handle_all(message: Message):
    if not message.from_user or message.from_user.is_bot: return
    cid, uid, today = str(message.chat.id), str(message.from_user.id), datetime.now().strftime("%Y-%m-%d")
    
    if cid not in db: db[cid] = {}
    if uid not in db[cid]: db[cid][uid] = {"name": message.from_user.full_name, "rep_history": [], "msg_history": []}
    db[cid][uid].setdefault("msg_history", []).append(today)
    db[cid][uid]["name"] = message.from_user.full_name
    save_data(DATA_FILE, db)

    if message.text:
        word = message.text.lower()
        if cid in filters and word in filters[cid]:
            f = filters[cid][word]
            if f.get("photo"): await message.answer_photo(f["photo"], caption=f["text"] or "")
            else: await message.answer(f["text"])

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
