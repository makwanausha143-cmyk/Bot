import os
import sqlite3
import re
from flask import Flask
from threading import Thread
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)

# ---------------- CONFIG ----------------
TOKEN = "8835968464:AAGjhE8p4KPd2fGUNoJCc3ZM8RwaqxCzGy8"
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

# ડેટાબેઝ સેટઅપ
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS msg_logs (chat_id INTEGER, message_id INTEGER)')
conn.commit()

app = Flask(__name__)

# ---------------- HELPER FUNCTIONS ----------------
def save_message(chat_id, message_id):
    cursor.execute('INSERT INTO msg_logs VALUES (?, ?)', (chat_id, message_id))
    conn.commit()

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(text="📲 Join Group", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("નમસ્તે! હું તમારી શું મદદ કરી શકું? નીચે આપેલ બટન પર ક્લિક કરો.", reply_markup=keyboard)

# ---------------- CALLBACK HANDLER ----------------
async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    target_chat_id = int(data[1])
    target_msg_id = int(data[2])

    try:
        await context.bot.delete_message(chat_id=target_chat_id, message_id=target_msg_id)
        await query.edit_message_text(text="🗑️ મેસેજ સફળતાપૂર્વક ડિલીટ થઈ ગયો છે.")
    except Exception as e:
        await query.edit_message_text(text=f"❌ ભૂલ: {e}")

# ---------------- MAIN MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message

    if not message: return

    # 1. કોન્ટેક્ટ શેરિંગ
    if message.contact:
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=f"👤 યુઝર: {message.from_user.first_name}\n📞 નંબર: {message.contact.phone_number}")
        await message.reply_text("આભાર! નંબર મળી ગયો છે.", reply_markup=ReplyKeyboardRemove())
        return

    # 2. એડમિન રિપ્લાય લોજિક
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
        target_id = GROUP_ID if "ગ્રુપમાં નવો મેસેજ:" in original_msg else None
        
        if not target_id:
            id_match = re.search(r"ID:\s*(\d+)", original_msg)
            if id_match: target_id = int(id_match.group(1))

        if target_id:
            try:
                sent_msg = await context.bot.copy_message(chat_id=target_id, from_chat_id=chat.id, message_id=message.message_id, protect_content=True)
                keyboard = [[InlineKeyboardButton("Delete 🗑️", callback_data=f"del_{target_id}_{sent_msg.message_id}")]]
                await message.reply_text("✅ મેસેજ મોકલી દીધો છે.", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # 3. ગ્રુપ અથવા પ્રાઈવેટ મેસેજ ફોરવર્ડિંગ
    info = f"👤 નામ: {message.from_user.first_name}\n🆔 ID: {message.from_user.id}\n💬 મેસેજ:"
    if chat.id == GROUP_ID: info = f"💬 ગ્રુપમાં નવો મેસેજ:\n" + info
    
    await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id, caption=info)

# ---------------- FLASK & MAIN ----------------
@app.route("/")
def home(): return "Bot is running!"

def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    app_bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ ગયો છે...")
    app_bot.run_polling()
        
