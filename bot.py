import json
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions

# --- НАЛАШТУВАННЯ ---
TOKEN = "8571874406:AAFw4X1B9GGfOluteAPkRMvoTYxlgG2bdd0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файли бази даних
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

# Завантаження даних
reputation = load_data(REP_FILE)
stats = load_data(STATS_FILE)
filters = load_data(FILTERS_FILE)

# Парсер часу (1h, 30m, 1d)
def parse_duration(time_str: str):
    try:
        unit = time_str[-1].lower()
        value = int(time_str[:-1])
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
    except:
        return None
    return None

# --- КОМАНДИ АДМІНІСТРАТОРА ---

async def is_admin(message: Message):
    member = await message.chat.get_member(message.from_user.id)
    return member.status in ["administrator", "creator"]

@dp.message(Command("ban"))
async def ban_cmd(message: Message, command: CommandObject):
    if not await is_admin(message): return
    if not message.reply_to_message: return await message.answer("Відповіжте на повідомлення порушника!")
    
    # /ban 1h причина
    args = command.args.split(maxsplit=1) if command.args else []
    duration = parse_duration(args[0]) if args else None
    reason = args[1] if len(args) > 1 else "Порушення правил"
    
    until = datetime.now() + duration if duration else None
    await message.chat.ban(user_id=message.reply_to_message.from_user.id, until_date=until)
    await message.answer(f"🔨 Користувач забанений! \nПричина: {reason}")

@dp.message(Command("mute"))
async def mute_cmd(message: Message, command: CommandObject):
    if not await is_admin(message): return
    if not message.reply_to_message: return await message.answer("Відповіжте на повідомлення порушника!")
    
    args = command.args.split(maxsplit=1) if command.args else []
    duration = parse_duration(args[0]) if args else timedelta(hours=1)
    reason = args[1] if len(args) > 1 else "Неадекватність"
    
    until = datetime.now() + duration
    await message.chat.restrict(
        user_id=message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await message.answer(f"🔇 Мут на {args[0] if args else '1h'}. \nПричина: {reason}")

@dp.message(Command("filter"))
async def add_filter(message: Message, command: CommandObject):
    if not await is_admin(message): return
    if not message.reply_to_message or not command.args:
        return await message.answer("Приклад: /filter [слово] (у відповідь на текст/фото)")
    
    trigger = command.args.lower()
    photo_id = message.reply_to_message.photo[-1].file_id if message.reply_to_message.photo else None
    text = message.reply_to_message.text or message.reply_to_message.caption
    
    filters[trigger] = {"text": text, "photo": photo_id}
    save_data(FILTERS_FILE, filters)
    await message.answer(f"✅ Фільтр на '{trigger}' додано!")

@dp.message(Command("filters"))
async def list_filters(message: Message):
    if not filters: return await message.answer("Список фільтрів порожній.")
    await message.answer("Активні фільтри: " + ", ".join(filters.keys()))

# --- РЕПУТАЦІЯ ТА СТАТИСТИКА ---

@dp.message(Command("start"))
async def start(message: Message):
    text = (
        f"Вітаємо, {message.from_user.mention_html()}! 👩‍🌾\n\n"
        f"Ти знайшов свій дім у <b>Hay Day</b> ✨\n"
        f"Наш чат — найкраще місце для:\n"
        f"📦 Обміну товарами (забудь про дефіцит!)\n"
        f"💡 Порад від досвідчених фермерів\n"
        f"📢 Новин про події та оновлення\n"
        f"🇺🇦 Мова чату українська!\n\n"
        f"Почни спілкування просто зараз!"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "+")
async def rep_plus(message: Message):
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    reputation[uid] = reputation.get(uid, 0) + 1
    save_data(REP_FILE, reputation)
    await message.answer(f"Красава! +1 до карми. Тепер у тебе {reputation[uid]}\n🏆 Твій рівень поваги: {reputation[uid]}")

@dp.message(F.text == "-")
async def rep_minus(message: Message):
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    reputation[uid] = reputation.get(uid, 0) - 1
    save_data(REP_FILE, reputation)
    await message.answer(f"Ех... -1 до карми. Тепер у тебе {reputation[uid]}\n📉 Твій рівень поваги впав.")

@dp.message(Command("toprep"))
async def top_rep(message: Message):
    sorted_rep = sorted(reputation.items(), key=lambda x: x[1], reverse=True)[:20]
    msg = "🏆 <b>ТОП-20 репутації:</b>\n\n"
    for i, (uid, val) in enumerate(sorted_rep, 1):
        msg += f"{i}. 👤 ID {uid} — <b>{val}</b>\n"
    await message.answer(msg, parse_mode="HTML")

@dp.message(Command("statistics"))
async def show_stats(message: Message):
    uid = str(message.from_user.id)
    count = stats.get(uid, 0)
    await message.answer(f"📊 Кількість ваших повідомлень: {count}")

@dp.message(Command("statisticsreset"))
async def reset_stats(message: Message):
    if not await is_admin(message): return
    stats.clear()
    save_data(STATS_FILE, stats)
    await message.answer("🗑 Статистику повідомлень скинуто!")

# --- ОБРОБНИК ВСІХ ПОВІДОМЛЕНЬ ---
@dp.message()
async def global_handler(message: Message):
    # Рахуємо статс
    uid = str(message.from_user.id)
    stats[uid] = stats.get(uid, 0) + 1
    save_data(STATS_FILE, stats)

    # Перевірка фільтрів
    if message.text:
        word = message.text.lower()
        if word in filters:
            f = filters[word]
            if f["photo"]:
                await message.answer_photo(f["photo"], caption=f["text"] or "")
            else:
                await message.answer(f["text"])

async def main():
    print("Бот запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
