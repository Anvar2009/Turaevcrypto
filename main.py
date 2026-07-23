import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8208919639:AAGTlgHBY8isrfDAykBpY1-OB2_Jngnvajc"
ADMIN_ID = 6337366278  # O'zingizning Telegram ID-ingizni kiriting

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_db():
    return sqlite3.connect("taz_bot.db")

# Admin uchun log yuboruvchi funksiya
async def send_log(text):
    try:
        await bot.send_message(ADMIN_ID, f"🔔 <b>LOG:</b>\n{text}", parse_mode="HTML")
    except Exception as e:
        print(f"Log yuborishda xatolik: {e}")

# /start komandasi
@dp.message(Command("start"))
def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        asyncio.create_task(send_log(f"🆕 Yangi foydalanuvchi kirdi: @{username} (ID: {user_id})"))

    conn.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Balans va Hamyon", callback_data="balance")],
        [InlineKeyboardButton(text="📝 TAZ Ishlash (Vazifalar)", callback_data="tasks")],
        [InlineKeyboardButton(text="🔄 TAZ Swap (Almashtirish)", callback_data="swap")],
        [InlineKeyboardButton(text="📤 Pul Yechib Olish", callback_data="withdraw")]
    ])
    
    if user_id == ADMIN_ID:
        kb.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])

    message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        f"<b>TAZ Ecosystem</b> botiga xush kelibsiz.\n"
        f"Vazifalarni bajarib <b>TAZ</b> ishlang va ularni USDT, TON, BTC, ETH valyutalariga almashtirib hamyoningizga yechib oling!",
        parse_mode="HTML",
        reply_markup=kb
    )

# BALANS BO'LIMI
@dp.callback_query(F.data == "balance")
async def show_balance(call: types.CallbackQuery):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT taz_balance, usdt_balance, ton_balance, btc_balance, eth_balance FROM users WHERE user_id = ?", (call.from_user.id,))
    u = cursor.fetchone()
    conn.close()

    text = (
        f"💳 <b>Sizning Hamyoningiz:</b>\n\n"
        f"🪙 TAZ: <b>{u[0]} TAZ</b>\n"
        f"💵 USDT: <b>{u[1]}</b>\n"
        f"💎 TON: <b>{u[2]}</b>\n"
        f"🟠 BTC: <b>{u[3]}</b>\n"
        f"🔷 ETH: <b>{u[4]}</b>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_home")]]))

# VAZIFALAR BO'LIMI
@dp.callback_query(F.data == "tasks")
async def show_tasks(call: types.CallbackQuery):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    
    buttons = []
    for t in tasks:
        # Bajarilganini tekshirish
        cursor.execute("SELECT * FROM user_tasks WHERE user_id = ? AND task_id = ?", (call.from_user.id, t[0]))
        if not cursor.fetchone():
            buttons.append([InlineKeyboardButton(text=f"{t[1]} (+{t[3]} TAZ)", callback_data=f"do_task_{t[0]}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_home")])
    conn.close()

    if len(buttons) == 1:
        await call.message.edit_text("🎉 Hozircha barcha vazifalarni bajarib bo'ldingiz!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await call.message.edit_text("📝 <b>Mavjud vazifalar:</b>\nVazifani tanlang va bajaring:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# VAZIFANI BAJARISH VAZIFASI
@dp.callback_query(F.data.startswith("do_task_"))
async def complete_task(call: types.CallbackQuery):
    task_id = int(call.data.split("_")[2])
    user_id = call.from_user.id

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if task:
        # TAZ balansiga qo'shish
        cursor.execute("UPDATE users SET taz_balance = taz_balance + ? WHERE user_id = ?", (task[3], user_id))
        cursor.execute("INSERT INTO user_tasks VALUES (?, ?)", (user_id, task_id))
        conn.commit()

        await call.answer(f"✅ Sizga {task[3]} TAZ berildi!", show_alert=True)
        await send_log(f"✅ Foydalanuvchi @{call.from_user.username} '{task[1]}' vazifasini bajarib {task[3]} TAZ oldi.")
    
    conn.close()
    await show_tasks(call)

# SWAP (ALMASHTIRISH)
@dp.callback_query(F.data == "swap")
async def swap_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="TAZ ➡️ USDT", callback_data="swap_USDT")],
        [InlineKeyboardButton(text="TAZ ➡️ TON", callback_data="swap_TON")],
        [InlineKeyboardButton(text="TAZ ➡️ BTC", callback_data="swap_BTC")],
        [InlineKeyboardButton(text="TAZ ➡️ ETH", callback_data="swap_ETH")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_home")]
    ])
    await call.message.edit_text("🔄 <b>TAZ tokenini qaysi valyutaga almashtirmoqchisiz?</b>", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith("swap_"))
async def process_swap(call: types.CallbackQuery):
    crypto = call.data.split("_")[1]
    user_id = call.from_user.id

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT taz_balance FROM users WHERE user_id = ?", (user_id,))
    taz = cursor.fetchone()[0]

    cursor.execute("SELECT rate FROM rates WHERE crypto = ?", (crypto,))
    rate = cursor.fetchone()[0]

    if taz >= 10:  # Minimum 10 TAZ almashtirish mumkin
        converted = taz * rate
        cursor.execute("UPDATE users SET taz_balance = 0 WHERE user_id = ?", (user_id,))
        cursor.execute(f"UPDATE users SET {crypto.lower()}_balance = {crypto.lower()}_balance + ? WHERE user_id = ?", (converted, user_id))
        conn.commit()

        await call.answer(f"✅ {taz} TAZ -> {converted} {crypto} ga almashtirildi!", show_alert=True)
        await send_log(f"🔄 SWAP: @{call.from_user.username} {taz} TAZ ni {converted} {crypto} ga almashtirdi.")
    else:
        await call.answer("❌ Almashtirish uchun kamida 10 TAZ kerak!", show_alert=True)

    conn.close()
    await show_balance(call)

# ADMIN PANEL
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id != "6337366278":
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi Vazifa Qo'shish", callback_data="add_task")],
        [InlineKeyboardButton(text="📊 Valyuta Kurslarini Sozlash", callback_data="set_rates")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_home")]
    ])
    await call.message.edit_text("⚙️ <b>Admin Panel</b>", parse_mode="HTML", reply_markup=kb)

# ORQAGA TUGMASI
@dp.callback_query(F.data == "back_home")
async def back_home(call: types.CallbackQuery):
    await cmd_start(call.message)

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
