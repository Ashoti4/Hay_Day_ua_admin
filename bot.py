import json, os, asyncio, random
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

DATA_FILE, FILTERS_FILE = "bot_data.json", "filters.json"

def load_data(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

db, filters = load_data(DATA_FILE), load_data(FILTERS_FILE)

def get_user_link(uid, name): return hlink(name, f"tg://user?id={uid}")
def get_footer(): return f"\n\n🏠 {hlink('@hayday18pluS', CHAT_LINK)}"

async def is_admin(message: Message):
    try:
        m = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return m.status in ('administrator', 'creator')
    except: return False

# --- ПРИВІТАННЯ/ПРОЩАННЯ ---
@dp.message(F.new_chat_members)
async def welcome(msg: Message):
    for m in msg.new_chat_members:
        if m.is_bot: continue
        txt = f"{m.mention_html()}, 👋 ласкаво просимо в HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌿🔞\n\nТут без цензури, зате з гумором і підтримкою 😉\nПочувайся як вдома!"
        await msg.answer(f"{txt}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.left_chat_member)
async def goodbye(msg: Message):
    txt = f"🌬 {msg.left_chat_member.full_name} втік(ла) з ферми... Певно, коза в дупу боднула"
    await msg.answer(f"{txt}{get_footer()}", parse_mode="HTML", disable_web_page_preview=True)

# --- РЕПУТАЦІЯ ---
@dp.message(F.text.in_({"+", "-"}))
async def change_rep(msg: Message):
    if not msg.reply_to_message or msg.reply_to_message.from_user.is_bot or msg.reply_to_message.from_user.id == msg.from_user.id: return
    cid, uid, today = str(msg.chat.id), str(msg.reply_to_message.from_user.id), datetime.now().strftime("%Y-%m-%d")
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.reply_to_message.from_user.full_name, "rep_history": [], "msg_history": []})
    if msg.text == "+":
        db[cid][uid]["rep_history"].append(today)
        act, emo = "отримав +1 до репутації!", "👍"
    else:
        if db[cid][uid]["rep_history"]: db[cid][uid]["rep_history"].pop()
        act, emo = "втратив -1 від репутації!", "👎"
    save_data(DATA_FILE, db)
    total = len(db[cid][uid]["rep_history"])
    await msg.answer(f"{emo} {get_user_link(uid, db[cid][uid]['name'])} {act}\nРепутація тут: <b>{total}</b>{get_footer()}", parse_mode="HTML")

# --- КОМАНДИ ---
@dp.message(Command("toprep"))
async def top_rep(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], u, len(d.get("rep_history", []))) for u, d in db.get(cid, {}).items() if d.get("rep_history")], key=lambda x: x[2], reverse=True)[:20]
    res = "🏆 <b>ТОП-20 репутації:</b>\n\n" + "\n".join([f"{i+1}. {get_user_link(u, n)} — <b>{s}</b>" for i, (n, u, s) in enumerate(items)])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

@dp.message(Command("toprepm"))
async def top_rep_m(msg: Message, command: CommandObject):
    try:
        cid, args = str(msg.chat.id), command.args.replace(".", "-").split()
        s_dt, e_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res_list = []
        for u, d in db.get(cid, {}).items():
            cnt = sum(1 for x in d.get("rep_history", []) if s_dt <= datetime.strptime(x, "%Y-%m-%d") <= e_dt)
            if cnt > 0: res_list.append((d["name"], u, cnt))
        res_list.sort(key=lambda x: x[2], reverse=True)
        out = f"🗓 <b>ТОП репутації ({args[0]} - {args[1]}):</b>\n\n" + "\n".join([f"{i+1}. {get_user_link(u, n)} — <b>{s}</b>" for i, (n, u, s) in enumerate(res_list[:20])])
        await msg.answer(f"{out if res_list else 'Немає даних.'}{get_footer()}", parse_mode="HTML")
    except: await msg.answer("Формат: /toprepm 2026.02.20 2026.02.23")

@dp.message(Command("statistics"))
async def stats(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], u, len(d.get("msg_history", []))) for u, d in db.get(cid, {}).items() if d.get("msg_history")], key=lambda x: x[2], reverse=True)[:20]
    res = "📊 <b>ТОП-20 активності:</b>\n\n" + "\n".join([f"{i+1}. {get_user_link(u, n)} — <b>{c}</b>" for i, (n, u, c) in enumerate(items)])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

@dp.message(Command("statisticsm"))
async def stats_m(msg: Message, command: CommandObject):
    try:
        cid, args = str(msg.chat.id), command.args.replace(".", "-").split()
        s_dt, e_dt = datetime.strptime(args[0], "%Y-%m-%d"), datetime.strptime(args[1], "%Y-%m-%d")
        res_list = []
        for u, d in db.get(cid, {}).items():
            cnt = sum(1 for x in d.get("msg_history", []) if s_dt <= datetime.strptime(x, "%Y-%m-%d") <= e_dt)
            if cnt > 0: res_list.append((d["name"], u, cnt))
        res_list.sort(key=lambda x: x[2], reverse=True)
        out = f"🗓 <b>Активність ({args[0]} - {args[1]}):</b>\n\n" + "\n".join([f"{i+1}. {get_user_link(u, n)} — <b>{s}</b>" for i, (n, u, s) in enumerate(res_list[:20])])
        await msg.answer(f"{out if res_list else 'Немає даних.'}{get_footer()}", parse_mode="HTML")
    except: await msg.answer("Формат: /statisticsm 2026.02.20 2026.02.24")

@dp.message(Command("filter"))
async def set_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args or not msg.reply_to_message: return
    cid, trigger = str(msg.chat.id), command.args.lower()
    filters.setdefault(cid, {})[trigger] = {"text": msg.reply_to_message.text or msg.reply_to_message.caption, "photo": msg.reply_to_message.photo[-1].file_id if msg.reply_to_message.photo else None}
    save_data(FILTERS_FILE, filters); await msg.answer(f"✅ Фільтр '{trigger}' збережено!")

@dp.message(Command("filters"))
async def list_filt(msg: Message):
    if not await is_admin(msg): return
    f_list = "\n".join([f"- <code>{f}</code>" for f in filters.get(str(msg.chat.id), {}).keys()])
    await msg.answer(f"<b>Фільтри чату:</b>\n{f_list if f_list else 'Порожньо.'}", parse_mode="HTML")

@dp.message(Command("stop"))
async def stop_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg): return
    cid, trigger = str(msg.chat.id), command.args.lower() if command.args else ""
    if filters.get(cid, {}).pop(trigger, None):
        save_data(FILTERS_FILE, filters); await msg.answer(f"🚫 Фільтр '{trigger}' видалено!")
    else: await msg.answer("Не знайдено.")

# --- ОБРОБНИК ---
@dp.message()
async def main_handler(msg: Message):
    if not msg.from_user or msg.from_user.is_bot: return
    cid, uid, today = str(msg.chat.id), str(msg.from_user.id), datetime.now().strftime("%Y-%m-%d")
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.from_user.full_name, "rep_history": [], "msg_history": []})
    db[cid][uid]["msg_history"].append(today); db[cid][uid]["name"] = msg.from_user.full_name; save_data(DATA_FILE, db)
    if msg.text and (f := filters.get(cid, {}).get(msg.text.lower())):
        if f.get("photo"): await msg.answer_photo(f["photo"], caption=f["text"] or "")
        else: await msg.answer(f["text"])

async def start(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(start())
