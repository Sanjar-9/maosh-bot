import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1003904454208      # Sizning kanal ID
MY_TELEGRAM_ID = 323634120       # Sizning Telegram ID
MAX_SEARCH_ID = 200              # Kanalda qidiradigan xabar soni

# Oylar ro'yxati
MONTHS = [
    "01.2026", "02.2026", "03.2026", "04.2026",
    
]

# ===================== LOGGING =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== HOLATLAR =====================
CHOOSING_MONTH = 1


def is_authorized(user_id: int) -> bool:
    return user_id == MY_TELEGRAM_ID


def get_month_keyboard():
    keyboard = []
    row = []
    for i, month in enumerate(MONTHS):
        row.append(month)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Sizga ruxsat yo'q!")
        return ConversationHandler.END

    await update.message.reply_text(
        "Выберите нужный месяц с помощью кнопок внизу. Для завершения сессии нажмите /start",
        reply_markup=get_month_keyboard()
    )
    return CHOOSING_MONTH


async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Sizga ruxsat yo'q!")
        return ConversationHandler.END

    chosen_month = update.message.text.strip()

    if chosen_month not in MONTHS:
        await update.message.reply_text(
            "⚠️ Iltimos, pastdagi tugmalardan birini tanlang.",
            reply_markup=get_month_keyboard()
        )
        return CHOOSING_MONTH

    await update.message.reply_text(f" {chosen_month} ")

    found_text = None
    try:
        for msg_id in range(1, MAX_SEARCH_ID + 1):
            try:
                fwd = await context.bot.forward_message(
                    chat_id=MY_TELEGRAM_ID,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id,
                    disable_notification=True
                )
                if fwd.text and chosen_month in fwd.text:
                    found_text = fwd.text
                    await context.bot.delete_message(MY_TELEGRAM_ID, fwd.message_id)
                    break
                else:
                    await context.bot.delete_message(MY_TELEGRAM_ID, fwd.message_id)
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Xato: {e}")

    if found_text:
        await update.message.reply_text(f"✅ {chosen_month} maoshi:\n\n{found_text}")
    else:
        await update.message.reply_text(
            f"❌ {chosen_month} uchun ma'lumot topilmadi.\n"
        
        )

    keyboard = ReplyKeyboardMarkup([["🔄 Qayta boshlash"]], resize_keyboard=True)
    await update.message.reply_text("Boshqa oy uchun:", reply_markup=keyboard)
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi. /start yozing.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🔄 Qayta boshlash$"), restart),
        ],
        states={
            CHOOSING_MONTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_salary)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("✅ Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
