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

# --- ПРИВІТАННЯ ТА ПРОЩАННЯ ---
@dp.message(F.new_chat_members)
async def welcome(message: Message):
    user_name = message.new_chat_members[0].mention_html()
    welcome_text = (
        f"{user_name}, 👋 ласкаво просимо в HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞\n\n"
        f"Тут без цензури, зате з гумором і підтримкою 😉\n"
        f"Почувайся як вдома. Якщо потрібна допомога — питай, ми не кусаємось (ну, майже😼)"
    )
    await message.answer(f"{welcome_text}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.left_chat_member)
async def goodbye(message: Message):
    user_name = message.left_chat_member.full_name
    bye_texts = [
        f"💨 {user_name} втік(ла) з ферми... Певно, Грег налякав.",
        f"🚜 {user_name} поїхав(ла) на іншу ферму. Повертайся ще!",
        f"👋 Мінус один у курилці. Бувай, {user_name}!"
    ]
    await message.answer(f"{random.choice(bye_texts)}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

# --- РЕПУТАЦІЯ ("+") ---
@dp.message(F.text == "+")
async def add_rep(message: Message):
    if not message.reply_to_message: return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id or target.is_bot: return
    
    uid = str(target.id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in db: 
        db[uid] = {"name": target.full_name, "rep_history": [], "msg_history": []}
    
    db[uid].setdefault("rep_history", [])
    db[uid]["rep_history"].append(today)
    db[uid]["name"] = target.full_name
    save_data(DATA_FILE, db)
    
    total_rep = len(db[uid]["rep_history"])
    resp = f"👍 {get_user_link(uid, target.full_name)} отримав +1 до репутації!\nТвоя репутація: <b>{total_rep}</b>"
    await message.answer(f"{resp}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

# --- ТОПИ РЕПУТАЦІЇ ---
@dp.message(Command("toprep"))
async def top_total(message: Message):
    items = [(data["name"], uid, len(data.get("rep_history", []))) for uid, data in db.items() if len(data.get("rep_history", [])) > 0]
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "🏆 <b>ТОП-20 репутації за весь час:</b>\n\n"
    for i, (name, uid, score) in enumerate(items[:20], 1):
        msg += f"{i}. {get_user_link(uid, name)} — <b>{score}</b>\n"
    await message.answer(f"{msg if items else 'ТОП порожній.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("toprepm"))
async def top_period(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer(f"Формат: <code>/toprepm 2026.01.01 2026.12.31</code>{get_footer()}", parse_mode="HTML")
    try:
        args = command.args.replace(".", "-").split()
        start_dt, end_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res = []
        for uid, data in db.items():
            count = sum(1 for d in data.get("rep_history", []) if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt)
            if count > 0: res.append((data["name"], uid, count))
        res.sort(key=lambda x: x[2], reverse=True)
        msg = f"🗓 <b>ТОП репутації за період {args[0]} — {args[1]}:</b>\n\n"
        for i, (name, uid, s) in enumerate(res[:20], 1): msg += f"{i}. {get_user_link(uid, name)} — <b>{s}</b>\n"
        await message.answer(f"{msg if res else 'Даних немає.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)
    except: await message.answer("Помилка формату дат! РРРР.ММ.ДД")

# --- СТАТИСТИКА ПОВІДОМЛЕНЬ ---
@dp.message(Command("statistics"))
async def stats_total(message: Message):
    items = [(data["name"], uid, len(data.get("msg_history", []))) for uid, data in db.items() if len(data.get("msg_history", [])) > 0]
    items.sort(key=lambda x: x[2], reverse=True)
    msg = "📊 <b>Статистика повідомлень за весь час:</b>\n\n"
    for i, (name, uid, count) in enumerate(items[:20], 1):
        msg += f"{i}. {get_user_link(uid, name)} — <b>{count}</b>\n"
    await message.answer(f"{msg if items else 'Статистика порожня.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("statisticsm"))
async def stats_period_msg(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        return await message.answer(f"Формат: <code>/statisticsm 2026.01.01 2026.12.31</code>{get_footer()}", parse_mode="HTML")
    try:
        args = command.args.replace(".", "-").split()
        start_dt, end_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res = []
        for uid, data in db.items():
            count = sum(1 for d in data.get("msg_history", []) if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt)
            if count > 0: res.append((data["name"], uid, count))
        res.sort(key=lambda x: x[2], reverse=True)
        msg = f"🗓 <b>Статистика повідомлень за {args[0]} — {args[1]}:</b>\n\n"
        for i, (name, uid, s) in enumerate(res[:20], 1): msg += f"{i}. {get_user_link(uid, name)} — <b>{s}</b>\n"
        await message.answer(f"{msg if res else 'За цей період повідомлень немає.'}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)
    except: await message.answer("Помилка формату дат! РРРР.ММ.ДД")

# --- ФІЛЬТРИ ---
@dp.message(Command("filters"))
async def show_filters(message: Message):
    chat_id = str(message.chat.id)
    if chat_id not in filters or not filters[chat_id]:
        return await message.answer(f"Список фільтрів порожній.{get_footer()}", parse_mode="HTML")
    list_f = "\n".join([f"- <code>{word}</code>" for word in filters[chat_id].keys()])
    header = "<b>Список фільтрів у HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞:</b>\n"
    await message.answer(f"{header}{list_f}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("filter"))
async def set_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if not command.args or not message.reply_to_message:
        return await message.answer("Відповідай на повідомлення командою <code>/filter слово</code>", parse_mode="HTML")
    trigger = command.args.lower()
    if chat_id not in filters: filters[chat_id] = {}
    filters[chat_id][trigger] = {
        "text": message.reply_to_message.text or message.reply_to_message.caption,
        "photo": message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None
    }
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр '<b>{trigger}</b>' збережено!", parse_mode="HTML")

@dp.message(Command("stop"))
async def stop_filter(message: Message, command: CommandObject):
    chat_id = str(message.chat.id)
    if not command.args: 
        return await message.answer("Вкажи слово для видалення: <code>/stop слово</code>")
    trigger = command.args.lower()
    if chat_id in filters and trigger in filters[chat_id]:
        del filters[chat_id][trigger]
        save_data(FILTERS_FILE, filters)
        await message.answer(f"🚫 Фільтр '<b>{trigger}</b>' видалено та зупинено!", parse_mode="HTML")
    else:
        await message.answer("Такого фільтра не знайдено.")

# --- ОБРОБНИК ПОВІДОМЛЕНЬ ---
@dp.message()
async def handle_all(message: Message):
    if not message.from_user or message.from_user.is_bot: return
    uid, today = str(message.from_user.id), datetime.now().strftime("%Y-%m-%d")
    
    if uid not in db: db[uid] = {"name": message.from_user.full_name, "rep_history": [], "msg_history": []}
    db[uid].setdefault("msg_history", [])
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
