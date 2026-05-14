import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# TOKEN
# =========================
TOKEN = os.getenv("TOKEN")

# =========================
# MOD
# =========================
current_mode = "all"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# ADMIN KONTROL
# =========================
def is_admin(status):
    return status in ["administrator", "creator"]


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )

    return is_admin(member.status)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Edit Silme Botu Aktif\n\n"
        "Komutlar için /help yaz."
    )


# =========================
# HELP
# =========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📌 Komutlar\n\n"
        "/mode text → Sadece yazı editlerini siler\n"
        "/mode media → Sadece medya editlerini siler\n"
        "/mode all → Tüm editleri siler\n\n"
        "/status → Aktif modu gösterir\n"
        "/help → Yardım menüsü\n\n"
        "⚠ Özellikler:\n"
        "• Fake editleri silmez\n"
        "• İsim/tag değişince mesajları silmez\n"
        "• Gerçek editleri siler"
    )

    await update.message.reply_text(text)


# =========================
# MODE
# =========================
async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_mode

    admin = await check_admin(update, context)

    if not admin:
        await update.message.reply_text(
            "❌ Bu komutu sadece admin kullanabilir."
        )
        return

    if len(context.args) == 0:
        await update.message.reply_text(
            "Kullanım:\n"
            "/mode text\n"
            "/mode media\n"
            "/mode all"
        )
        return

    mode = context.args[0].lower()

    if mode not in ["text", "media", "all"]:
        await update.message.reply_text("❌ Geçersiz mod.")
        return

    current_mode = mode

    await update.message.reply_text(
        f"✅ Mod değiştirildi: {mode}"
    )


# =========================
# STATUS
# =========================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📌 Aktif mod: {current_mode}"
    )


# =========================
# EDIT KONTROL
# =========================
async def handle_edited(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edited = update.edited_message

    if not edited:
        return

    is_text = bool(edited.text)

    is_media = bool(
        edited.photo
        or edited.video
        or edited.document
        or edited.audio
        or edited.voice
        or edited.animation
        or edited.sticker
    )

    should_delete = False

    if current_mode == "all":
        should_delete = True

    elif current_mode == "text" and is_text:
        should_delete = True

    elif current_mode == "media" and is_media:
        should_delete = True

    if not should_delete:
        return

    try:
        await edited.delete()

        await context.bot.send_message(
            chat_id=edited.chat.id,
            text=(
                f"🗑 Editlenen mesaj silindi\n"
                f"👤 {edited.from_user.full_name}"
            ),
        )

    except Exception as e:
        print(e)


# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        print("TOKEN bulunamadı!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("status", status_command))

    app.add_handler(
        MessageHandler(
            filters.UpdateType.EDITED_MESSAGE,
            handle_edited,
        )
    )

    print("✅ Bot çalışıyor...")

    app.run_polling()


if __name__ == "__main__":
    main()
