#pip install python-telegram-bot==21.6

import json
import os

from telegram import Update
from telegram.ext import (
ApplicationBuilder,
ContextTypes,
MessageHandler,
filters,
CommandHandler
)
from telegram.constants import ChatMemberStatus

import os
TOKEN = os.getenv("BOT_TOKEN")

CACHE_FILE = "cache.json"
SETTINGS_FILE = "settings.json"

------------------------

#LOAD / SAVE

def load_json(file):
if os.path.exists(file):
try:
with open(file, "r", encoding="utf-8") as f:
return json.load(f)
except:
return {}
return {}

def save_json(file, data):
with open(file, "w", encoding="utf-8") as f:
json.dump(data, f)

message_cache = load_json(CACHE_FILE)
settings = load_json(SETTINGS_FILE)

def save_all():
save_json(CACHE_FILE, message_cache)
save_json(SETTINGS_FILE, settings)

------------------------

def get_settings(chat_id):
chat_id = str(chat_id)

if chat_id not in settings:  
    settings[chat_id] = {  
        "mode": "all",          # all | text | media  
        "apply_admins": True  
    }  
    save_all()  

return settings[chat_id]

------------------------

async def is_admin(bot, chat_id, user_id):
member = await bot.get_chat_member(chat_id, user_id)
return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

def extract_content(msg):
if msg.text:
return ["text", msg.text]

if msg.caption:  
    return ["caption", msg.caption]  

if msg.photo:  
    return ["media", "photo"]  

if msg.video:  
    return ["media", "video"]  

if msg.document:  
    return ["media", "document"]  

if msg.audio:  
    return ["media", "audio"]  

if msg.voice:  
    return ["media", "voice"]  

if msg.animation:  
    return ["media", "gif"]  

if msg.video_note:  
    return ["media", "video_note"]  

return ["other", None]

def is_service(msg):
return any([
msg.new_chat_members,
msg.left_chat_member,
msg.new_chat_title,
msg.new_chat_photo
])

------------------------

#HELP

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("""
🤖 Edit Koruma Botu

⚙️ /mode all | text | media
→ Edit koruma modu

👮 /admins on | off
→ Adminleri koru/kapat

📊 /status
→ Ayarları gösterir

❓ /help
→ Komutlar
""")

------------------------

#STATUS

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
cfg = get_settings(update.message.chat_id)

await update.message.reply_text(  
    f"Mode: {cfg['mode']}\nAdminlerde: {'Açık' if cfg['apply_admins'] else 'Kapalı'}"  
)

------------------------

#MODE

async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.message

if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):  
    return  

if not context.args:  
    await msg.reply_text("Kullanım: /mode all | text | media")  
    return  

mode = context.args[0].lower()  

if mode not in ["all", "text", "media"]:  
    await msg.reply_text("Seçenekler: all, text, media")  
    return  

cfg = get_settings(msg.chat_id)  
cfg["mode"] = mode  
save_all()  

await msg.reply_text(f"Mode: {mode}")

------------------------

#ADMINS

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.message

if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):  
    return  

if not context.args:  
    await msg.reply_text("Kullanım: /admins on | off")  
    return  

val = context.args[0].lower()  

if val not in ["on", "off"]:  
    await msg.reply_text("Seçenekler: on / off")  
    return  

cfg = get_settings(msg.chat_id)  
cfg["apply_admins"] = (val == "on")  
save_all()  

await msg.reply_text(f"Admin koruma: {val}")

------------------------

#CACHE (normal mesaj)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.message
if not msg:
return

if is_service(msg):  
    return  

chat_id = str(msg.chat_id)  
msg_id = str(msg.message_id)  

message_cache.setdefault(chat_id, {})  
message_cache[chat_id][msg_id] = extract_content(msg)  

save_json(CACHE_FILE, message_cache)

------------------------

#EDIT KORUMA (ASIL KISIM)

async def edited_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.edited_message
if not msg:
return

chat_id = str(msg.chat_id)  
msg_id = str(msg.message_id)  

cfg = get_settings(chat_id)  

if is_service(msg):  
    return  

if msg.from_user:  
    if not cfg["apply_admins"]:  
        if await is_admin(context.bot, int(chat_id), msg.from_user.id):  
            return  

new_content = extract_content(msg)  
old_content = message_cache.get(chat_id, {}).get(msg_id)  

if not old_content:  
    message_cache.setdefault(chat_id, {})[msg_id] = new_content  
    save_json(CACHE_FILE, message_cache)  
    return  

# 🔥 SADECE GERÇEK EDIT  

async def edited_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_message
    if not msg:
        return

    chat_id = str(msg.chat_id)
    msg_id = str(msg.message_id)

    cfg = get_settings(chat_id)

    if is_service(msg):
        return

    # admin bypass
    if msg.from_user and cfg["apply_admins"]:
        if await is_admin(context.bot, int(chat_id), msg.from_user.id):
            return

    new_content = extract_content(msg)
    old_content = message_cache.get(chat_id, {}).get(msg_id)

    # ❗ daha önce hiç kayıt yoksa çık
    if not old_content:
        return

    # ❗ gerçekten değişmişse sil
    if new_content != old_content:
        try:
            await context.bot.delete_message(int(chat_id), int(msg_id))
        except:
            pass

        # cache güncelle
        message_cache[chat_id][msg_id] = new_content
        save_json(CACHE_FILE, message_cache)
        
------------------------

#BOT

app = ApplicationBuilder().token(TOKEN).build()

#KOMUTLAR

app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("mode", mode_cmd))
app.add_handler(CommandHandler("admins", admins_cmd))

#NORMAL MESAJ

app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, message_handler))

#EDIT

app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_handler))

print("Bot çalışıyor...")
app.run_polling()
