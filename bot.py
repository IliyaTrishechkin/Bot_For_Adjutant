import os
import json
import string
import secrets
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram.error import NetworkError, TelegramError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters


load_dotenv(Path(__file__).parent / 'data.env', encoding='UTF-8')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_USER = json.loads((Path(__file__).parent / 'user.json').read_text(encoding='utf-8'))
REGISTRATION, PASS = range(100, 102)



def up_date():
    global DATA_USER
    DATA_USER = json.loads((Path(__file__).parent / 'user.json').read_text(encoding='utf-8'))


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def IS_password():
    for key in DATA_USER["PASSWORD"]:
        if DATA_USER["PASSWORD"][key] is None:
            DATA_USER["PASSWORD"][key] = generate_password()
    with open('user.json', 'w', encoding='utf-8') as f:
        json.dump(DATA_USER, f, ensure_ascii=False, indent=4)
    up_date()


def get_status(uid):
    statuses = []
    for key, value in DATA_USER["Users"].items():
        if not value:
            continue
        if str(uid) in value:
            statuses.append(key)
    return statuses


async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [  [InlineKeyboardButton("Учень", callback_data="reg_Student")],
            [InlineKeyboardButton("Писарь", callback_data="reg_Clerk")],
            [InlineKeyboardButton("Ад'ютант", callback_data="reg_Ajutant")],
            [InlineKeyboardButton("Вчитель", callback_data="reg_Teacher")]
        ]
    await update.message.reply_text("Доброго дня,\nоберіть ваше становище.", reply_markup=InlineKeyboardMarkup(kb))


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    status = context.user_data.get("status", "—")
    if text == DATA_USER["PASSWORD"][status]:
        with open('user.json', 'r', encoding='utf-8') as f:
            ud = json.load(f)
        if status == "Teachers":
            ud["Users"][status].append(str(update.effective_user.id))
        else:
            ud["Users"][status] = [str(update.effective_user.id)]
            ud["PASSWORD"][status] = generate_password()
        with open('user.json', 'w', encoding='utf-8') as f:
            json.dump(ud, f, ensure_ascii=False, indent=4)
        await update.message.reply_text("Ви зареестровані. Визвіть /start")
        return ConversationHandler.END
    await update.message.reply_text("Невірний пароль. Визвіть /registration та зарееструйтесь знов.")
    return ConversationHandler.END



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        uid = str(update.effective_user.id)
    else:
        uid = str(update.effective_chat.id)
        if not uid in DATA_USER["Users"]["Student"]:
            with open('user.json', 'r', encoding='utf-8') as f:
                ud = json.load(f)

            ud["Users"]["Student"].append(str(uid))

            with open('id_users.json', 'w', encoding='utf-8') as f:
                json.dump(ud, f, ensure_ascii=False, indent=4)
            up_date()
    
    if not uid in DATA_USER["Users"]["Student"] and not uid in DATA_USER["Users"]["Teacher"]:
        await registration(update, context)  
        return
    
    status = get_status(uid)
    if "Student" in status:
        kb = [  
            [InlineKeyboardButton("Переглянути минуле дз", callback_data="Student|homework")],
            [InlineKeyboardButton("Проекти та позакласні завдання", callback_data="Student|project")]
        ]
        text = "Привіт, учень,\nя допоможу тобі у вирішенні твоїх справ."
    if "Adjutant" in status:
        kb += []
        text = "Привіт, ад'ютант,\nя допоможу тобі у вирішенні твоїх справ."
    if "Clerk" in status:
        kb += []
        text = "Привіт, писарь,\nя допоможу тобі у вирішенні твоїх справ."
    if "Teacher" in status:
        kb = []
        text = "Привіт, Вчитель,\nя допоможу тобі у вирішенні твоїх справ."

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


async def on_registration_menu_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = str(update.effective_user.id)
    
    if q.data != "reg_Teacher":
        if not user_id in DATA_USER["Users"]["Student"]:
            with open('user.json', 'r', encoding='utf-8') as f:
                ud = json.load(f)

            ud["Users"]["Student"].append(str(user_id))

            with open('user.json', 'w', encoding='utf-8') as f:
                json.dump(ud, f, ensure_ascii=False, indent=4)
            
            up_date()
    
    match q.data:
        case "reg_Student":
            await q.edit_message_text("Ви успішно зарееструвались як учень.")
            return ConversationHandler.END
        case "reg_Clerk":
            context.user_data["status"] = "Clerk"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отрімати пароль.")
            return REGISTRATION
        case "reg_Ajutant":
            context.user_data["status"] = "Adjutant"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отрімати пароль.")
            return REGISTRATION
        case "reg_Teacher":
            context.user_data["status"] = "Teacher"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отрімати пароль.")
            return REGISTRATION


async def Clic_Button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cmd, arg = q.data.split("|")
    match cmd:
        case "Student":
            pass
        case "Clerk":
            pass
        case "Adjutant":
            pass
        case "Teacher":
            pass
        case "Admin":
            pass




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()


    IS_password()


    conv_registration = ConversationHandler(
        entry_points = [CallbackQueryHandler(on_registration_menu_pressed, pattern="^reg_")],
        states={
            REGISTRATION:[MessageHandler(filters.TEXT & ~filters.COMMAND, password)]
        },
        fallbacks=[],
    )


    app.add_handler(conv_registration)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registration", registration))
    app.add_handler(CallbackQueryHandler(on_registration_menu_pressed, pattern="^reg_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, password))

    app.run_polling(drop_pending_updates=True)