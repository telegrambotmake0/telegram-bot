# pip install python-telegram-bot==21.6 flask

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

from flask import Flask
from threading import Thread

# ------------------------
# BOT TOKEN
TOKEN = os.getenv("BOT_TOKEN")

# ------------------------
# WEB SERVER (7/24 UYUMAMA)
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot aktif!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ------------------------
# FILES
CACHE_FILE = "cache.json"
SETTINGS_FILE = "settings.json"

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

# ------------------------
# SETTINGS
def get_settings(chat_id):
    chat_id = str(chat_id)

    if chat_id not in settings:
        settings[chat_id] = {
            "mode": "all",
            "apply_admins": True
        }
        save_all()

    return settings[chat_id]

# ------------------------
# ADMIN CHECK
async def is_admin(bot, chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

# ------------------------
# CONTENT
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

# ------------------------
# COMMANDS
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
🤖 Edit Koruma Botu

⚙️ /mode all | text | media
👮 /admins on | off
📊 /status
""")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_settings(update.message.chat_id)
    await update.message.reply_text(
        f"Mode: {cfg['mode']}\nAdmin koruma: {cfg['apply_admins']}"
    )

async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        return

    if not context.args:
        return await msg.reply_text("Kullanım: /mode all | text | media")

    mode = context.args[0]

    if mode not in ["all", "text", "media"]:
        return await msg.reply_text("all / text / media")

    cfg = get_settings(msg.chat_id)
    cfg["mode"] = mode
    save_all()

    await msg.reply_text(f"Mode: {mode}")

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        return

    if not context.args:
        return await msg.reply_text("on / off")

    val = context.args[0]

    cfg = get_settings(msg.chat_id)
    cfg["apply_admins"] = (val == "on")
    save_all()

    await msg.reply_text(f"Admin koruma: {val}")

# ------------------------
# MESSAGE CACHE
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or is_service(msg):
        return

    chat_id = str(msg.chat_id)
    msg_id = str(msg.message_id)

    message_cache.setdefault(chat_id, {})
    message_cache[chat_id][msg_id] = extract_content(msg)

    save_json(CACHE_FILE, message_cache)

# ------------------------
# EDIT DELETE CORE
async def edited_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_message
    if not msg:
        return

    chat_id = str(msg.chat_id)
    msg_id = str(msg.message_id)

    cfg = get_settings(chat_id)

    if is_service(msg):
        return

    if msg.from_user and cfg["apply_admins"]:
        if await is_admin(context.bot, int(chat_id), msg.from_user.id):
            return

    new_content = extract_content(msg)
    old_content = message_cache.get(chat_id, {}).get(msg_id)

    if not old_content:
        message_cache.setdefault(chat_id, {})[msg_id] = new_content
        save_json(CACHE_FILE, message_cache)
        return

    if new_content == old_content:
        return

    try:
        await context.bot.delete_message(int(chat_id), int(msg_id))
    except:
        pass

    message_cache[chat_id][msg_id] = new_content
    save_json(CACHE_FILE, message_cache)

# ------------------------
# BOT START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("mode", mode_cmd))
app.add_handler(CommandHandler("admins", admins_cmd))

app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, message_handler))
app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_handler))

print("Bot çalışıyor...")

keep_alive()   # 🔥 7/24 açık tutma

app.run_polling()
