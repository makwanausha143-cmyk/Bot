import os
import re
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# લોગિંગ ચાલુ કરો જેથી ભૂલ ખબર પડે
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------------- CONFIG ----------------
TOKEN = "8835968464:AAHgkDrHqcDrNHKK7pq-vaA7L467eEOT_uM"
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

app = Flask(__name__)

# મેસેજ ડિલીટ કરવા માટેનું ફંક્શન
async def delete_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"ડિલીટ કરવામાં ભૂલ: {e}")

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Start command received!")
    button = KeyboardButton(text="join group", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("join group ઉપર ક્લિક કરો ત્યારબાદ લિંક ન મળે તો મેસેજ કરો", reply_markup=keyboard)

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    try:
        await context.bot.delete_message(chat_id=int(data[1]), message_id=int(data[2]))
        await query.edit_message_text(text="🗑️ મેસેજ ડિલીટ કરી દેવાયો છે.")
    except Exception as e:
        await query.edit_message_text(text=f"❌ ભૂલ: {e}")

# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message: return

    # કોન્ટેક્ટ હેન્ડલિંગ
    if message.contact:
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=f"👤 યુઝર: {message.from_user.first_name}\n📞 નંબર: {message.contact.phone_number}")
        try: await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
        except: pass
        return

    # એડમિન રિપ્લાય
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
        target_id = GROUP_ID if "ગ્રુપમાં નવો મેસેજ:" in original_msg else None
        id_match = re.search(r"ID:\s*(\d+)", original_msg)
        if id_match: target_id = int(id_match.group(1))

        if target_id:
            try:
                text_content = message.text or message.caption or ""
                sent_msg = None
                if message.photo:
                    sent_msg = await context.bot.send_photo(chat_id=target_id, photo=message.photo[-1].file_id, caption=text_content, protect_content=True, has_spoiler=True)
                elif message.video:
                    sent_msg = await context.bot.send_video(chat_id=target_id, video=message.video.file_id, caption=text_content, protect_content=True, has_spoiler=True)
                elif message.document:
                    sent_msg = await context.bot.send_document(chat_id=target_id, document=message.document.file_id, caption=text_content, protect_content=True)
                elif message.text:
                    sent_msg = await context.bot.send_message(chat_id=target_id, text=text_content, protect_content=True)

                if sent_msg:
                    context.job_queue.run_once(delete_msg, 10, chat_id=target_id, data=sent_msg.message_id)
                    keyboard = [[InlineKeyboardButton("Delete 🗑️", callback_data=f"del_{target_id}_{sent_msg.message_id}")]]
                    await message.reply_text("✅ મેસેજ મોકલી દીધો છે (10 સેકન્ડમાં ઓટો ડિલીટ).", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # ગ્રુપ અને યુઝર મેસેજ
    if chat.id == GROUP_ID:
        caption = f"💬 ગ્રુપમાં નવો મેસેજ:\n👤 નામ: {message.from_user.first_name}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=GROUP_ID, message_id=message.message_id, caption=caption if not message.text else None)
    elif chat.id != YOUR_CHAT_ID:
        info = f"👤 નામ: {message.from_user.first_name}\n🆔 ID: {message.from_user.id}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id, caption=info if not message.text else None)

# ---------------- FLASK & MAIN ----------------
@app.route("/")
def home(): return "Bot is running!"

def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    
    # Application બિલ્ડ કરો
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # હેન્ડલર્સ ઉમેરો
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    all_media = filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.CONTACT
    app_bot.add_handler(MessageHandler(all_media & (~filters.COMMAND), handle_message))
    
    print("🚀 બોટ શરૂ થઈ રહ્યો છે... ટર્મિનલ લોગ તપાસો.")
    app_bot.run_polling()
