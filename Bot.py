import os
import re
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, CommandHandler, 
    ContextTypes, CallbackQueryHandler,
)

# ---------------- CONFIG ----------------
TOKEN = "8835968464:AAGjhE8p4KPd2fGUNoJCc3ZM8RwaqxCzGy8"
YOUR_CHAT_ID = 5306025504

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("chat_history.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history 
                      (user_id INTEGER, name TEXT, message TEXT, sender_type TEXT)''')
    conn.commit()
    conn.close()

def save_message(user_id, name, text, sender_type):
    conn = sqlite3.connect("chat_history.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (user_id, name, text, sender_type))
    conn.commit()
    conn.close()

def get_full_history(user_id):
    conn = sqlite3.connect("chat_history.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT name, message, sender_type FROM history WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

init_db()
app = Flask(__name__)

# ---------------- BOT LOGIC ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message: return

    # ૧. એડમિન રિપ્લાય (યુઝરને મોકલવા માટે)
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_text = message.reply_to_message.caption or message.reply_to_message.text or ""
        id_match = re.search(r"ID:\s*(\d+)", original_text)
        
        if id_match:
            target_id = int(id_match.group(1))
            # યુઝરને મેસેજ મોકલો
            sent_msg = await context.bot.send_message(chat_id=target_id, text=f"💬 એડમિન: {message.text}")
            save_message(target_id, "Admin", message.text, "Admin")
            
            # ડિલીટ બટન સાથે કન્ફર્મેશન
            kb = [[InlineKeyboardButton("🗑️ ડિલીટ કરો", callback_data=f"del_{target_id}_{sent_msg.message_id}")]]
            await message.reply_text("✅ જવાબ મોકલાઈ ગયો છે.", reply_markup=InlineKeyboardMarkup(kb))
        return

    # ૨. યુઝરનો મેસેજ
    if chat.id != YOUR_CHAT_ID:
        user_name = message.from_user.first_name
        user_id = message.from_user.id
        text = message.text or "Media/Other"
        save_message(user_id, user_name, text, "User")
        
        info = f"👤 નામ: {user_name}\n🆔 ID: {user_id}\n💬 મેસેજ: {text}"
        kb = [[InlineKeyboardButton("📜 હિસ્ટ્રી જુઓ", callback_data=f"hist_{user_id}")]]
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=info, reply_markup=InlineKeyboardMarkup(kb))

# ---------------- CALLBACKS ----------------
async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("_") # del_user_id_msg_id
    try:
        await context.bot.delete_message(chat_id=int(data[1]), message_id=int(data[2]))
        await query.edit_message_text("🗑️ મેસેજ ડિલીટ કરી દેવાયો છે.")
    except Exception as e:
        await query.answer(f"ભૂલ: {e}")

async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split("_")[1])
    messages = get_full_history(user_id)
    history_text = f"📜 યુઝર {user_id} ની ચેટ:\n\n"
    for name, msg, s_type in messages:
        history_text += f"{'👨‍💻' if s_type == 'Admin' else '👤'} {name}: {msg}\n"
    await query.edit_message_text(history_text)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    app_bot.add_handler(CallbackQueryHandler(history_callback, pattern="^hist_"))
    app_bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    print("બોટ સક્રિય છે...")
    app_bot.run_polling()
