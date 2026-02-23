import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8019231475  # ← ВСТАВЬ СВОЙ ID

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("casino.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 100,
    spins INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    today_spins INTEGER DEFAULT 0,
    last_spin TEXT
)
""")
conn.commit()

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("🎰 Крутить")
menu.add("💰 Баланс", "📊 Статистика")
menu.add("🏆 Топ сегодня")

def get_user(user):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
                   (user.id, user.username))
    conn.commit()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    get_user(message.from_user)
    await message.answer("🎰 Казино PRO 2.0", reply_markup=menu)

@dp.message_handler(lambda m: m.text == "💰 Баланс")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?",
                   (message.from_user.id,))
    bal = cursor.fetchone()[0]
    await message.answer(f"💰 Баланс: {bal} ⭐")

@dp.message_handler(lambda m: m.text == "📊 Статистика")
async def stats(message: types.Message):
    cursor.execute("SELECT spins, wins FROM users WHERE user_id=?",
                   (message.from_user.id,))
    spins, wins = cursor.fetchone()
    await message.answer(f"📊 Прокрутов: {spins}\n🏆 Побед: {wins}")

@dp.message_handler(lambda m: m.text == "🏆 Топ сегодня")
async def top_today(message: types.Message):
    cursor.execute("SELECT username, today_spins FROM users ORDER BY today_spins DESC LIMIT 5")
    top = cursor.fetchall()

    text = "🏆 ТОП 5 сегодня:\n\n"
    for i, user in enumerate(top, start=1):
        text += f"{i}. @{user[0]} — {user[1]} прокрутов\n"

    await message.answer(text)

@dp.message_handler(lambda m: m.text == "🎰 Крутить")
async def spin(message: types.Message):

    if not message.from_user.username:
        await message.answer("⚠ Установи username в профиле!")
        return

    get_user(message.from_user)

    dice = await bot.send_dice(message.chat.id, emoji="🎰")
    value = dice.dice.value
    reward = 0

    if value == 64:
        reward = 75
    elif value in [1,22,43]:
        reward = 40
    elif value in [16,32,48]:
        reward = 30
    elif value in [7,14,21]:
        reward = 25

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("UPDATE users SET spins = spins + 1, today_spins = today_spins + 1, last_spin=? WHERE user_id=?",
                   (today, message.from_user.id))

    if reward > 0:
        cursor.execute("UPDATE users SET balance = balance + ?, wins = wins + 1 WHERE user_id=?",
                       (reward, message.from_user.id))
        await message.answer(f"🎉 Победа! +{reward} ⭐")
    else:
        cursor.execute("UPDATE users SET balance = balance - 5 WHERE user_id=?",
                       (message.from_user.id,))
        await message.answer("😢 -5 ⭐")

    conn.commit()

@dp.message_handler(commands=['clear_stats'])
async def clear_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("UPDATE users SET today_spins = 0")
    conn.commit()
    await message.answer("Статистика очищена ✅")

if __name__ == "__main__":
    executor.start_polling(dp)
