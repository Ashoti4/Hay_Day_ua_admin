# --- ПОВНІСТТЮ ВИПРАВЛЕНИЙ КОД ---
import json, os, asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hlink

DB_DIR = "/app/data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DATA_FILE = f"{DB_DIR}/bot_data.json"
FILTERS_FILE = f"{DB_DIR}/filters.json"

TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
OWNER_USERNAME = "I_AM_ARMY_07"

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
def get_footer(): return f"\n\n🏠 Канал HAY DAY ua БОРДЕЛЬ-КУРІЛКА🌱🔞"

async def is_admin(message: Message):
    if message.from_user.username == OWNER_USERNAME: return True
    try:
        m = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return m.status in ('administrator', 'creator')
    except: return False

def find_user_by_tag(cid, tag):
    tag = tag.replace("@", "").lower()
    for uid, data in db.get(cid, {}).items():
        if data.get("username", "").lower() == tag: return uid
    return None

# --- КОМАНДИ РЕДАГУВАННЯ ---

@dp.message(Command("rm"))
async def manual_rep_month(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    try:
        args = command.args.split()
        user_tag, val, date_raw = args[0], int(args[1]), args[2]
        cid = str(msg.chat.id)
        uid = find_user_by_tag(cid, user_tag)
        if not uid: return await msg.answer("Користувача не знайдено.")
        date_str, month_prefix = f"{date_raw.replace('.', '-')}-01", date_raw.replace('.', '-')
        if val > 0:
            for _ in range(val): db[cid][uid]["rep_history"].append(date_str)
        elif val < 0:
            for _ in range(abs(val)):
                for i, d in enumerate(db[cid][uid]["rep_history"]):
                    if d.startswith(month_prefix):
                        db[cid][uid]["rep_history"].pop(i)
                        break
        save_data(DATA_FILE, db); await msg.answer(f"✅ Репутація {user_tag} за {date_raw} змінена!")
    except: await msg.answer("Формат: /rm @user +5 2026.04")

@dp.message(Command("sm"))
async def manual_stats_month(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    try:
        args = command.args.split()
        user_tag, val, date_raw = args[0], int(args[1]), args[2]
        cid = str(msg.chat.id)
        uid = find_user_by_tag(cid, user_tag)
        if not uid: return await msg.answer("Користувача не знайдено.")
        date_str, month_prefix = f"{date_raw.replace('.', '-')}-01", date_raw.replace('.', '-')
        if val > 0:
            for _ in range(val): db[cid][uid]["msg_history"].append(date_str)
        elif val < 0:
            for _ in range(abs(val)):
                for i, d in enumerate(db[cid][uid]["msg_history"]):
                    if d.startswith(month_prefix):
                        db[cid][uid]["msg_history"].pop(i)
                        break
        save_data(DATA_FILE, db); await msg.answer(f"📊 Статистика {user_tag} за {date_raw} змінена!")
    except: await msg.answer("Формат: /sm @user +10 2026.04")

@dp.message(Command("r"))
async def manual_rep(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    try:
        args = command.args.split()
        user_tag, val = args[0], int(args[1])
        cid, today = str(msg.chat.id), datetime.now().strftime("%Y-%m-%d")
        uid = find_user_by_tag(cid, user_tag)
        if not uid: return await msg.answer("Користувача не знайдено.")
        if val > 0:
            for _ in range(val): db[cid][uid]["rep_history"].append(today)
        elif val < 0:
            for _ in range(abs(val)):
                if db[cid][uid]["rep_history"]: db[cid][uid]["rep_history"].pop()
        save_data(DATA_FILE, db); await msg.answer(f"✅ Репутація {user_tag} змінена!")
    except: await msg.answer("Формат: /r @user +5")

@dp.message(Command("s"))
async def manual_stats(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    try:
        args = command.args.split()
        user_tag, val = args[0], int(args[1])
        cid, today = str(msg.chat.id), datetime.now().strftime("%Y-%m-%d")
        uid = find_user_by_tag(cid, user_tag)
        if not uid: return await msg.answer("Користувача не знайдено.")
        if val > 0:
            for _ in range(val): db[cid][uid]["msg_history"].append(today)
        elif val < 0:
            for _ in range(abs(val)):
                if db[cid][uid]["msg_history"]: db[cid][uid]["msg_history"].pop()
        save_data(DATA_FILE, db); await msg.answer(f"📊 Повідомлення {user_tag} змінені!")
    except: await msg.answer("Формат: /s @user +50")

# --- ФІЛЬТРИ (ВИПРАВЛЕНО) ---

@dp.message(Command("filter"))
async def set_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args or not msg.reply_to_message: return
    cid, trigger = str(msg.chat.id), command.args.lower().strip()
    filters.setdefault(cid, {})[trigger] = {
        "text": msg.reply_to_message.text or msg.reply_to_message.caption,
        "photo": msg.reply_to_message.photo[-1].file_id if msg.reply_to_message.photo else None
    }
    save_data(FILTERS_FILE, filters)
    await msg.answer(f"✅ Фільтр '{trigger}' збережено!")

@dp.message(Command("stop"))
async def stop_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    cid, trigger = str(msg.chat.id), command.args.lower().strip()
    if cid in filters and trigger in filters[cid]:
        del filters[cid][trigger]
        save_data(FILTERS_FILE, filters)
        await msg.answer(f"🚫 Фільтр '{trigger}' видалено!")
    else:
        await msg.answer(f"❌ Фільтр '{trigger}' не знайдено.")

# --- РЕПУТАЦІЯ (АВТО) ---

@dp.message(F.text.in_({"+", "-"}))
async def change_rep_auto(msg: Message):
    if not msg.reply_to_message or msg.reply_to_message.from_user.is_bot or msg.reply_to_message.from_user.id == msg.from_user.id: return
    cid, uid = str(msg.chat.id), str(msg.reply_to_message.from_user.id)
    now = datetime.now()
    today, current_month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.reply_to_message.from_user.full_name, "username": msg.reply_to_message.from_user.username, "rep_history": [], "msg_history": []})
    if msg.text == "+":
        db[cid][uid]["rep_history"].append(today)
        text = f"👍 {get_user_link(uid, db[cid][uid]['name'])} отримав +1!"
    else:
        if db[cid][uid]["rep_history"]: db[cid][uid]["rep_history"].pop()
        text = f"👎 {get_user_link(uid, db[cid][uid]['name'])} втратив -1!"
    save_data(DATA_FILE, db)
    m_rep = sum(1 for d in db[cid][uid]["rep_history"] if d.startswith(current_month))
    await msg.answer(f"{text}\nРепутація за місяць: <b>{m_rep}</b>{get_footer()}", parse_mode="HTML")

# --- ТОПИ ---

@dp.message(Command("toprep"))
async def top_rep(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], len(d.get("rep_history", []))) for u, d in db.get(cid, {}).items()], key=lambda x: x[1], reverse=True)[:20]
    res = "🏆 <b>ТОП-20 репутації:</b>\n\n" + "\n".join([f"{i+1}. {n} — <b>{s}</b>" for i, (n, s) in enumerate(items) if s > 0])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

@dp.message(Command("statistics"))
async def stats(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], len(d.get("msg_history", []))) for u, d in db.get(cid, {}).items()], key=lambda x: x[1], reverse=True)[:20]
    res = "📊 <b>ТОП-20 активності:</b>\n\n" + "\n".join([f"{i+1}. {n} — <b>{c}</b>" for i, (n, c) in enumerate(items) if c > 0])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

# --- ГОЛОВНИЙ ОБРОБНИК ---

@dp.message()
async def main_handler(msg: Message):
    if not msg.from_user or msg.from_user.is_bot: return
    cid, uid, today = str(msg.chat.id), str(msg.from_user.id), datetime.now().strftime("%Y-%m-%d")
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.from_user.full_name, "username": msg.from_user.username, "rep_history": [], "msg_history": []})
    db[cid][uid].update({"username": msg.from_user.username, "name": msg.from_user.full_name})
    db[cid][uid]["msg_history"].append(today); save_data(DATA_FILE, db)
    
    if msg.text:
        txt = msg.text.lower().strip()
        if f := filters.get(cid, {}).get(txt):
            if f.get("photo"): await msg.answer_photo(f["photo"], caption=(f["text"] or "") + get_footer(), parse_mode="HTML")
            else: await msg.answer(f"{f['text']}{get_footer()}", parse_mode="HTML")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
