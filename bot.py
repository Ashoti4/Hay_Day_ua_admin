import json, os, asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hlink

# --- ШЛЯХИ ТА КОНФІГУРАЦІЯ ---
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
    with open(file, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)

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

# --- КОМАНДИ РЕДАГУВАННЯ (RM, SM, R, S) ---

@dp.message(Command("rm"))
async def manual_rep_month(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    try:
        args = command.args.split()
        user_tag, val, date_raw = args[0], int(args[1]), args[2]
        cid = str(msg.chat.id)
        uid = find_user_by_tag(cid, user_tag)
        if not uid: return await msg.answer("Користувача не знайдено.")
        month_prefix = date_raw.replace('.', '-')
        if val > 0:
            for _ in range(val): db[cid][uid]["rep_history"].append(f"{month_prefix}-01")
        elif val < 0:
            for _ in range(abs(val)):
                for i, d in enumerate(db[cid][uid]["rep_history"]):
                    if d.startswith(month_prefix):
                        db[cid][uid]["rep_history"].pop(i); break
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
        month_prefix = date_raw.replace('.', '-')
        if val > 0:
            for _ in range(val): db[cid][uid]["msg_history"].append(f"{month_prefix}-01")
        elif val < 0:
            for _ in range(abs(val)):
                for i, d in enumerate(db[cid][uid]["msg_history"]):
                    if d.startswith(month_prefix):
                        db[cid][uid]["msg_history"].pop(i); break
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
    except: pass

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
    except: pass

# --- ФІЛЬТРИ ---

@dp.message(Command("filter"))
async def set_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args or not msg.reply_to_message: return
    cid, trigger = str(msg.chat.id), command.args.lower().strip()
    reply = msg.reply_to_message
    
    file_id, f_type = None, None
    if reply.photo: file_id, f_type = reply.photo[-1].file_id, "photo"
    elif reply.document: file_id, f_type = reply.document.file_id, "document"
    elif reply.video: file_id, f_type = reply.video.file_id, "video"
    elif reply.audio: file_id, f_type = reply.audio.file_id, "audio"
    elif reply.voice: file_id, f_type = reply.voice.file_id, "voice"
    elif reply.video_note: file_id, f_type = reply.video_note.file_id, "video_note"

    filters.setdefault(cid, {})[trigger] = {
        "text": reply.text or reply.caption,
        "file_id": file_id, "file_type": f_type
    }
    save_data(FILTERS_FILE, filters); await msg.answer(f"✅ Фільтр '{trigger}' збережено!")

@dp.message(Command("stop"))
async def stop_filt(msg: Message, command: CommandObject):
    if not await is_admin(msg) or not command.args: return
    cid, trigger = str(msg.chat.id), command.args.lower().strip()
    if cid in filters and filters[cid].pop(trigger, None):
        save_data(FILTERS_FILE, filters); await msg.answer(f"🚫 Фільтр '{trigger}' видалено!")
    else: await msg.answer("❌ Фільтр не знайдено.")

@dp.message(Command("filters"))
async def list_filters(msg: Message):
    cid = str(msg.chat.id)
    if cid in filters and filters[cid]:
        res = "📃 Список фільтрів:\n" + "\n".join([f"- {t}" for t in filters[cid].keys()])
        await msg.answer(res)
    else: await msg.answer("Фільтрів немає.")

# --- СИСТЕМА РЕПУТАЦІЇ ТА ОБРОБНИК ---

@dp.message(F.text.in_({"+", "-"}))
async def change_rep_auto(msg: Message):
    if not msg.reply_to_message or msg.reply_to_message.from_user.is_bot or msg.reply_to_message.from_user.id == msg.from_user.id: return
    cid, uid = str(msg.chat.id), str(msg.reply_to_message.from_user.id)
    now = datetime.now()
    today, cur_m = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
    
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.reply_to_message.from_user.full_name, "username": msg.reply_to_message.from_user.username, "rep_history": [], "msg_history": []})
    
    if msg.text == "+":
        db[cid][uid]["rep_history"].append(today)
        txt = f"👍 {get_user_link(uid, db[cid][uid]['name'])} отримав +1!"
    else:
        if db[cid][uid]["rep_history"]: db[cid][uid]["rep_history"].pop()
        txt = f"👎 {get_user_link(uid, db[cid][uid]['name'])} втратив -1!"
    
    save_data(DATA_FILE, db)
    m_rep = sum(1 for d in db[cid][uid]["rep_history"] if d.startswith(cur_m))
    await msg.answer(f"{txt}\nРепутація за місяць: <b>{m_rep}</b>{get_footer()}", parse_mode="HTML")

@dp.message(Command("toprep"))
async def top_rep(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], len(d.get("rep_history", []))) for u, d in db.get(cid, {}).items()], key=lambda x: x[1], reverse=True)[:20]
    res = "🏆 ТОП-20 репутації:\n\n" + "\n".join([f"{i+1}. {n} — {s}" for i, (n, s) in enumerate(items) if s > 0])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

# --- КОМАНДА /toprepm З НОВИМ ФОРМАТОМ ДАТ ---
@dp.message(Command("toprepm"))
async def top_rep_month(msg: Message, command: CommandObject):
    cid = str(msg.chat.id)
    now = datetime.now()
    
    if command.args:
        try:
            args = command.args.strip().split()
            if len(args) == 2:
                start_date = args[0].replace('.', '-')
                end_date = args[1].replace('.', '-')
            else:
                return await msg.answer("❌ Формат команди: `/toprepm РРРР.ММ.ДД РРРР.ММ.ДД`")
        except:
            return await msg.answer("❌ Невірний формат дат.")
    else:
        # Якщо аргументи відсутні, показуємо за поточний місяць
        start_date = now.strftime("%Y-%m-01")
        end_date = now.strftime("%Y-%m-%d")

    items = []
    for uid, d in db.get(cid, {}).items():
        period_rep = 0
        for date_str in d.get("rep_history", []):
            if start_date <= date_str <= end_date:
                period_rep += 1
        if period_rep > 0:
            items.append((d["name"], period_rep))
            
    items = sorted(items, key=lambda x: x[1], reverse=True)[:20]
    
    lbl_start = start_date.replace('-', '.')
    lbl_end = end_date.replace('-', '.')
    
    res = f"🏆 ТОП-20 репутації за період {lbl_start} — {lbl_end}:\n\n" + "\n".join([f"{i+1}. {n} — {s}" for i, (n, s) in enumerate(items)])
    await msg.answer(f"{res if items else f'За період з {lbl_start} по {lbl_end} даних немає.'}{get_footer()}", parse_mode="HTML")

@dp.message(Command("statistics"))
async def stats(msg: Message):
    cid = str(msg.chat.id)
    items = sorted([(d["name"], len(d.get("msg_history", []))) for u, d in db.get(cid, {}).items()], key=lambda x: x[1], reverse=True)[:20]
    res = "📊 ТОП-20 активності:\n\n" + "\n".join([f"{i+1}. {n} — {c}" for i, (n, c) in enumerate(items) if c > 0])
    await msg.answer(f"{res if items else 'Порожньо.'}{get_footer()}", parse_mode="HTML")

@dp.message()
async def main_handler(msg: Message):
    if not msg.from_user or msg.from_user.is_bot: return
    cid, uid, today = str(msg.chat.id), str(msg.from_user.id), datetime.now().strftime("%Y-%m-%d")
    
    db.setdefault(cid, {}).setdefault(uid, {"name": msg.from_user.full_name, "username": msg.from_user.username, "rep_history": [], "msg_history": []})
    db[cid][uid].update({"username": msg.from_user.username, "name": msg.from_user.full_name})
    db[cid][uid]["msg_history"].append(today); save_data(DATA_FILE, db)
    
    if msg.text:
        t = msg.text.lower().strip()
        if f := filters.get(cid, {}).get(t):
            cap = (f["text"] or "") + get_footer()
            fid, ftype = f.get("file_id"), f.get("file_type")
            if not fid: await msg.answer(cap, parse_mode="HTML")
            elif ftype == "photo": await msg.answer_photo(fid, caption=cap, parse_mode="HTML")
            elif ftype == "document": await msg.answer_document(fid, caption=cap, parse_mode="HTML")
            elif ftype == "video": await msg.answer_video(fid, caption=cap, parse_mode="HTML")
            elif ftype == "audio": await msg.answer_audio(fid, caption=cap, parse_mode="HTML")
            elif ftype == "voice": await msg.answer_voice(fid, caption=cap, parse_mode="HTML")
            elif ftype == "video_note": await msg.answer_video_note(fid)

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
