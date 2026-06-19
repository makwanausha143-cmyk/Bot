import os
import re
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes, CallbackQueryHandler

# --- કોન્ફિગરેશન ---
TOKEN = '8835968464:AAGLJz1EfAVzafHgqbnJ66uEQRR2dbBHhUk'
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

app = Flask(__name__)

# ૧. સ્ટાર્ટ કમાન્ડ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("નમસ્તે! હું બોટ છું. તમારી શું મદદ કરી શકું.")

# ૨. બટન ક્લિક હેન્ડલર (મેસેજ ડિલીટ કરવા માટે)
async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    target_chat_id = int(data[1])
    target_msg_id = int(data[2])
    
    try:
        await context.bot.delete_message(chat_id=target_chat_id, message_id=target_msg_id)
        await query.edit_message_text(text="🗑️ મેસેજ સામેવાળામાંથી ડિલીટ કરી દેવાયો છે.")
    except Exception as e:
        await query.edit_message_text(text=f"❌ ભૂલ: {e}")

# ૩. મુખ્ય હેન્ડલર
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    
    if not message:
        return

    # A. જો એડમિન (તમે) કોઈ મેસેજ પર રિપ્લાય આપો છો
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
        target_id = None
        
        if "ગ્રુપમાં નવો મેસેજ:" in original_msg:
            target_id = GROUP_ID
        else:
            id_match = re.search(r"ID:\s*(\d+)", original_msg)
            if id_match:
                target_id = int(id_match.group(1))

        if target_id:
            try:
                sent_msg = None
                text_content = message.text or message.caption or ""

                if message.photo:
                    sent_msg = await context.bot.send_photo(chat_id=target_id, photo=message.photo[-1].file_id, caption=text_content, protect_content=True)
                elif message.video:
                    sent_msg = await context.bot.send_video(chat_id=target_id, video=message.video.file_id, caption=text_content, protect_content=True)
                elif message.document:
                    sent_msg = await context.bot.send_document(chat_id=target_id, document=message.document.file_id, caption=text_content, protect_content=True)
                elif message.text:
                    sent_msg = await context.bot.send_message(chat_id=target_id, text=text_content, protect_content=True)

                if sent_msg:
                    keyboard = [[InlineKeyboardButton("Delete 🗑️", callback_data=f"del_{target_id}_{sent_msg.message_id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await message.reply_text(f"✅ મેસેજ મોકલી દીધો છે. ડિલીટ કરવા માટે બટન દબાવો.", reply_markup=reply_markup)
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # B. જો ગ્રુપમાંથી કોઈ મેસેજ આવે તો તમને મોકલે
    if chat.id == GROUP_ID:
        user_name = message.from_user.first_name
        caption = f"💬 ગ્રુપમાં નવો મેસેજ:\n👤 નામ: {user_name}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=GROUP_ID, message_id=message.message_id, caption=caption if not message.text else None)
        if message.text:
            await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=caption)
        return

    # C. જો કોઈ યુઝર પર્સનલમાં બોટને મેસેજ કરે
    if chat.id != YOUR_CHAT_ID:
        user_name = message.from_user.first_name
        user_id = message.from_user.id
        info = f"👤 નામ: {user_name}\n🆔 ID: {user_id}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id, caption=info if not message.text else None)
        if message.text:
            await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=info)

# Flask Server
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    
    all_media = (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL)
    app_bot.add_handler(MessageHandler(all_media & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ રહ્યો છે...")
    app_bot.run_polling(drop_pending_updates=True)
