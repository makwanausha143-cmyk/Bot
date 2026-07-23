import os
import re
import asyncio
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

# ---------------- CONFIG ----------------
TOKEN = "8835968464:AAEPAGE8kiqJBe3N6N7M_pNtTAwbCOA5djE"
YOUR_CHAT_ID = 5306025504
GROUP_ID = -1003912250139

app = Flask(__name__)

# ગ્રુપની માહિતી સેવ કરવા માટેની ડિક્શનરી (મેમરી)
# આમાં બોટ જે જે ગ્રુપમાં એડમિન હશે તેની યાદી રાખશે
REGISTERED_GROUPS = {}

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
        "join group ઉપર ક્લિક કરો ત્યારબાદ લિંક ન મળે તો મેસેજ કરો",
        reply_markup=keyboard
    )

# ---------------- ADMINS COMMAND (જે ગ્રુપમાં બોટ છે તેની યાદી મેળવવા) ----------------
async def check_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    # જો આ કમાન્ડ એડમિન પ્રાઇવેટ ચેટમાં આપે
    if chat.id == YOUR_CHAT_ID:
        if not REGISTERED_GROUPS:
            await update.message.reply_text("❌ હજુ સુધી બોટે કોઈપણ ગ્રુપની માહિતી નોંધી નથી. કૃપા કરીને ગ્રુપમાં જઈને એકવાર /admins કમાન્ડ મોકલો.")
            return
        
        text = "📋 **બોટ જે ગ્રુપમાં એડમિન છે તેની યાદી:**\n\n"
        for g_id, g_name in REGISTERED_GROUPS.items():
            text += f"📌 ગ્રુપ નામ: {g_name}\n🆔 ID: <code>{g_id}</code>\n-------------------\n"
        
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # જો કોઈ ગ્રુપમાં આ કમાન્ડ આપવામાં આવે, તો તે ગ્રુપને રજિસ્ટર કરી લો અને એડમિન્સની યાદી બતાવો
    if chat.type in ["group", "supergroup"]:
        try:
            # ગ્રુપનું નામ સેવ કરી લો
            REGISTERED_GROUPS[chat.id] = chat.title
            
            # ગ્રુપના એડમિન્સની લિસ્ટ મેળવો
            admins = await context.bot.get_chat_administrators(chat.id)
            admin_list = []
            for admin in admins:
                user = admin.user
                name = user.first_name
                if user.username:
                    admin_list.append(f"@{user.username} ({name})")
                else:
                    admin_list.append(name)
            
            admin_names = ", ".join(admin_list)
            await update.message.reply_text(
                f"✅ આ ગ્રુપ બોટમાં રજિસ્ટર થઈ ગયું છે!\n\n👑 **ગ્રુપ એડમિન્સ:**\n{admin_names}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ ભૂલ: {e}")

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
        try:
            await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
        except Exception as e:
            print(f"મેસેજ ડિલીટ કરવામાં ભૂલ: {e}")
        return
        
    # 2. એડમિન રિપ્લાય
    if chat.id == YOUR_CHAT_ID and message.reply_to_message:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
        
        target_id = None
        if "ગ્રુપમાં નવો મેસેજ:" in original_msg:
            target_id = GROUP_ID
        else:
            id_match = re.search(r"🆔 ID:\s*(\d+)", original_msg)
            if id_match:
                target_id = int(id_match.group(1))

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
                    await message.reply_text("✅ મેસેજ ગ્રુપમાં મોકલી દીધો છે.", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                await message.reply_text(f"❌ ભૂલ: {e}")
        return

    # 3. ગ્રુપ મેસેજ
    if chat.id == GROUP_ID:
        # ગ્રુપ ઓટોમેટિક રજિસ્ટર કરી લો
        REGISTERED_GROUPS[chat.id] = chat.title
        
        user = message.from_user
        user_mention = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        
        caption = (
            f"💬 ગ્રુપમાં નવો મેસેજ:\n"
            f"👤 મોકલનાર: {user.first_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"🔗 યુઝર: {user_mention}\n"
            f"💬 મેસેજ: {message.text or ''}"
        )
        
        await context.bot.copy_message(
            chat_id=YOUR_CHAT_ID, 
            from_chat_id=GROUP_ID, 
            message_id=message.message_id, 
            caption=caption if not message.text else None
        )
        if message.text: 
            await context.bot.send_message(
                chat_id=YOUR_CHAT_ID, 
                text=caption, 
                parse_mode="HTML"
            )
        return

    # 4. પ્રાઈવેટ યુઝર
    if chat.id != YOUR_CHAT_ID:
        info = f"👤 નામ: {message.from_user.first_name}\n🆔 ID: {message.from_user.id}\n💬 મેસેજ: {message.text or ''}"
        await context.bot.copy_message(chat_id=YOUR_CHAT_ID, from_chat_id=chat.id, message_id=message.message_id, caption=info if not message.text else None)
        if message.text: await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=info)

# ---------------- FLASK & MAIN ----------------
@app.route("/")
def home(): 
    return "Bot is running!"

def run_flask(): 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # કમાન્ડ હેન્ડલર્સ
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("admins", check_admins))
    
    app_bot.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    
    all_media = filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.CONTACT
    app_bot.add_handler(MessageHandler(all_media & (~filters.COMMAND), handle_message))
    
    print("બોટ શરૂ થઈ રહ્યો છે...")
    app_bot.run_polling(drop_pending_updates=True)
