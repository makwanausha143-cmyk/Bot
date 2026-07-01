import os
import re
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes, CallbackQueryHandler

# --- કોન્ફિગરેશન ---
TOKEN = '8835968464:AAF_TimXj5Vre_buXzhWYbV1VgMPxtjGSJk'
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

# ડેટાબેઝ સેટઅપ
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT)")
db.commit()

app = Flask(__name__)

# ૧. સ્ટાર્ટ કમાન્ડ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("નમસ્તે! હું તમારી શું મદદ કરી શકું !!!")

# ૨. બટન ક્લિક હેન્ડલર
async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    target_chat_id = int(data[1])
    target_msg_id = int(data[2])
    try:
        await context.bot.delete_message(chat_id=target_chat_id, message_id=target_msg_id)
        await query.edit_message_text(text="🗑️ મેસેજ ડિલીટ કરી દેવાયો છે.")
    except Exception as e:
        await query.edit_message_text(text=f"❌ ભૂલ: {e}")

# ૩. મુખ્ય હેન્ડલર
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    
    if not message: return

    # A. એડમિનનો જવાબ (Reply)
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_text = message.reply_to_message.text or ""
        id_match = re.search(r"🆔\s*(\d+)", original_text)
        
        target_id = GROUP_ID if "ગ્રુપમાં નવો મેસેજ" in original_text else (int(id_match.group(1)) if id_match else None)
        
        if target_id:
            try:
                sent_msg = await context.bot.send_message(chat_id=target_id, text=message.text or "કોઈ મેસેજ નથી", protect_content=True)
                keyboard = [[InlineKeyboardButton("Delete 🗑️", callback_data=f"del_{target_id}_{sent_msg.message_id}")]]
                await message.reply_text("✅ મેસેજ મોકલી દીધો છે.", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # B. ગ્રુપ અને યુઝર્સના મેસેજ (પર્સનલ મેસેજ માટે ડેટાબેઝમાં નામ સેવ થશે)
    if chat.id != YOUR_CHAT_ID:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        # ડેટાબેઝમાં યુઝર સેવ કરો
        cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", (user_id, user_name))
        db.commit()
        
        prefix = "💬 ગ્રુપમાં નવો મેસેજ" if chat.id == GROUP_ID else "👤 નવો પર્સનલ મેસેજ"
        info = f"{prefix}\n👤 નામ: {user_name}\n🆔 ID: `{user_id}`\n\n💬 મેસેજ: {message.text or 'કોઈ મીડિયા ફાઇલ'}"
        
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=info, parse_mode="Markdown")
        if not message.text:
            await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id)

# Flask Server
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    app_bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ રહ્યો છે...")
    app_bot.run_polling()
