import os
import re
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

# ---------------- CONFIG ----------------
TOKEN = "8835968464:AAGjhE8p4KPd2fGUNoJCc3ZM8RwaqxCzGy8"
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

app = Flask(__name__)

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(
        text="join group",
        request_contact=True
    )
    keyboard = ReplyKeyboardMarkup(
        [[button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "નમસ્તે! હું તમારી શું મદદ કરી શકું !!! join grup ઉપર ક્લિક કરો",
        reply_markup=keyboard
    )

# ---------------- DELETE BUTTON ----------------
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

# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message

    if not message:
        return

    # 1. જો યુઝરે કોન્ટેક્ટ શેર કર્યો હોય
    if message.contact:
        phone = message.contact.phone_number
        await context.bot.send_message(
            chat_id=YOUR_CHAT_ID,
            text=f"👤 યુઝર: {message.from_user.first_name}\n📞 નંબર: {phone}"
        )
        await message.reply_text("આભાર! તમારો નંબર મળી ગયો છે.", reply_markup=ReplyKeyboardRemove())
        return

    # 2. એડમિન રિપ્લાય
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
        target_id = GROUP_ID if "ગ્રુપમાં નવો મેસેજ:" in original_msg else None
        
        if not target_id:
            id_match = re.search(r"ID:\s*(\d+)", original_msg)
            if id_match: target_id = int(id_match.group(1))

        if target_id:
            try:
                text_content = message.text or message.caption or ""
                sent_msg = None
                
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
                    await message.reply_text("✅ મેસેજ મોકલી દીધો છે.", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # 3. ગ્રુપ મેસેજ
    if chat.id == GROUP_ID:
        caption = f"💬 ગ્રુપમાં નવો મેસેજ:\n👤 નામ: {message.from_user.first_name}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=GROUP_ID, message_id=message.message_id, caption=caption if not message.text else None)
        if message.text: await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=caption)
        return

    # 4. પ્રાઈવેટ યુઝર
    if chat.id != YOUR_CHAT_ID:
        info = f"👤 નામ: {message.from_user.first_name}\n🆔 ID: {message.from_user.id}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id, caption=info if not message.text else None)
        if message.text: await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=info)

# ---------------- FLASK & MAIN ----------------
@app.route("/")
def home(): return "Bot is running!"

def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    
    all_media = filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.CONTACT
    app_bot.add_handler(MessageHandler(all_media & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ રહ્યો છે...")
    app_bot.run_polling(drop_pending_updates=True)
