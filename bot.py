from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Бот работает!')


if __name__ == '__main__':
    application = Application.builder().token("YOUR_TOKEN").build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()