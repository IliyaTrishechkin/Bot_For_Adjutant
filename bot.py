
import os
import json
import string
import secrets
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram.error import NetworkError, TelegramError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters


load_dotenv(Path(__file__).parent / 'data.env', encoding='UTF-8')
TOKEN = "8448978111:AAFnd7ISDJRxfhP4uQE7rNdQ3HuDE8GK97I"
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_USER = json.loads((Path(__file__).parent / 'user.json').read_text(encoding='utf-8'))
REGISTRATION, PASS = range(100, 102)
HOMEWORK, SUBJECT, INPUT_HOMEWORK = range(3)



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
    status = context.user_data.get("status")

    
    if not status:
        await update.message.reply_text(
            "Сталася помилка. Спершу виберіть посаду через /registration"
        )
        return ConversationHandler.END
    

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
        up_date()
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
    
    if uid not in DATA_USER["Users"].get("Student", []) and uid not in DATA_USER["Users"].get("Teacher", []):
        await registration(update, context)  
        return
    
    status = get_status(uid)
    if "Student" in status:
        kb = [  
            [InlineKeyboardButton("Переглянути минуле дз", callback_data="Student|homework")],
            [InlineKeyboardButton("Проекти та позакласні завдання", callback_data="Student|project_1")],
            [InlineKeyboardButton("Розклад", callback_data="Student|schedule")]
        ]
        text = "Привіт, учень,\nя допоможу тобі у вирішенні твоїх справ."
    if "Adjutant" in status:
        kb = []
        text = "Привіт, ад'ютант,\nя допоможу тобі у вирішенні твоїх справ."
    if "Clerk" in status:
        kb = [
            [InlineKeyboardButton("Написати д/з", callback_data="Clerk|homework")],
            [InlineKeyboardButton("Написати завдання про проект чи позакласне завдання", callback_data="Clerk|project")],
            [InlineKeyboardButton("Переглянути минуле дз", callback_data="Student|homework")],
            [InlineKeyboardButton("Проекти та позакласні завдання", callback_data="Student|project_1")],
            [InlineKeyboardButton("Розклад", callback_data="Student|schedule")]
        ]
        text = "Привіт, писар,\nя допоможу тобі у вирішенні твоїх справ."
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
            await q.edit_message_text("Ви успішно зарееструвались як учень. Напишіть /start")
            return ConversationHandler.END
        case "reg_Clerk":
            context.user_data["status"] = "Clerk"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отримати пароль.")
            return REGISTRATION
        case "reg_Ajutant":
            context.user_data["status"] = "Adjutant"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отримати пароль.")
            return REGISTRATION
        case "reg_Teacher":
            context.user_data["status"] = "Teacher"
            await q.edit_message_text("Введіть пароль для цієї посади.\nЗвернітся до адміна щоб отримати пароль.")
            return REGISTRATION


async def Clic_Button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cmd, arg = q.data.split("|")
    match cmd:
        case "Student":
            match arg:
                case "homework":
                    await homework(update, context)
                case "project_1":
                    await q.message.edit_text("Ось твої проекти та позакласні завдання:")
                case "schedule":
                    with open("schedule.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    text = ""
                    for day, lessons in data.items():
                        text += f"*{day}:*\n"
                        for lesson in lessons:
                            text += f"Урок {lesson['урок']}: {lesson['предмет']}\n"
                        text += "\n"
                    
                    kb = [[InlineKeyboardButton("Назад", callback_data="Student|Back")]]

                    await q.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(kb),
                        parse_mode="Markdown"
                    )
                case "today_homework":
                    await homework_today(update, context)
                case "tomorrow_homework":
                    await homework_tomorrow(update, context)
                    pass
                case "project":
                    pass
                case "extracurricular_tasks":
                    pass
                case "Back":
                    kb = [  
                        [InlineKeyboardButton("Переглянути минуле дз", callback_data="Student|homework")],
                        [InlineKeyboardButton("Проекти та позакласні завдання", callback_data="Student|project_1")],
                        [InlineKeyboardButton("Розклад", callback_data="Student|schedule")]
                    ]

                    await update.callback_query.message.edit_text(
                        "Привіт, писар,\nя допоможу тобі у вирішенні твоїх справ.",
                        reply_markup=InlineKeyboardMarkup(kb)
                    )
        case "Clerk":
            match arg:
                case "homework":
                    return await start_create_homework(update, context)
                case "Back":
                    kb = [
                        [InlineKeyboardButton("Написати д/з", callback_data="Clerk|homework")],
                        [InlineKeyboardButton("Написати завдання про проект чи позакласне завдання", callback_data="Clerk|project")],
                        [InlineKeyboardButton("Переглянути минуле дз", callback_data="Student|homework")],
                        [InlineKeyboardButton("Проекти та позакласні завдання", callback_data="Student|project_1")],
                        [InlineKeyboardButton("Розклад", callback_data="Student|schedule")]
                    ]

                    await update.callback_query.message.edit_text(
                        "Привіт, писар,\nя допоможу тобі у вирішенні твоїх справ.",
                        reply_markup=InlineKeyboardMarkup(kb)
                    )
        case "Adjutant":
            pass
        case "Teacher":
            pass
        case "Admin":
            pass



async def homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [  
        [InlineKeyboardButton("Сьогоднішні д/з", callback_data="Student|today_homework")],
        [InlineKeyboardButton("Д/з на завтра", callback_data="Student|tomorrow_homework")],
        [InlineKeyboardButton("Назад", callback_data="Student|Back")]
    ]
    
    await update.callback_query.message.edit_text(
        text="Обери яке домашнє завдання хочеш подивитись",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    
async def homework_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # Визначаємо сьогоднішній день у форматі JSON
    day_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday"
    }

    today_index = datetime.today().weekday()  # 0 = понеділок, 4 = п’ятниця
    day_key = day_map.get(today_index)
    
    with open("hometask.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    text = f"*Домашнє завдання на сьогодні:*\n\n"
    for lesson in data[day_key]:
        homework = lesson["д/з"] if lesson["д/з"] else "немає"
        text += f"{lesson['предмет']}: {homework}\n"

    await q.message.edit_text(text, parse_mode="Markdown")


async def homework_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # Визначаємо сьогоднішній день у форматі JSON
    day_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday"
    }

    today_index = datetime.today().weekday()+1  # 0 = понеділок, 4 = п’ятниця
    day_key = day_map.get(today_index)
    
    with open("hometask.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    text = f"*Домашнє завдання на завтра:*\n\n"
    for lesson in data[day_key]:
        homework = lesson["д/з"] if lesson["д/з"] else "немає"
        text += f"{lesson['предмет']}: {homework}\n"

    await q.message.edit_text(text, parse_mode="Markdown")


async def project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [  
        [InlineKeyboardButton("Проекти", callback_data="Student|project")],
        [InlineKeyboardButton("Позакласні завдання", callback_data="Student|extracurricular_tasks")],
        [InlineKeyboardButton("Назад у меню", callback_data="Student|Back")]
    ]
    
    await update.callback_query.edit_message_text(
        text="Обери що саме хочеш подивитись",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def create_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Понеділок", callback_data="Clerk|monday")],
        [InlineKeyboardButton("Вівторок", callback_data="Clerk|tuesday")],
        [InlineKeyboardButton("Середа", callback_data="Clerk|wednesday")],
        [InlineKeyboardButton("Четверг", callback_data="Clerk|thursday")],
        [InlineKeyboardButton("П'ятниця", callback_data="Clerk|friday")],
        [InlineKeyboardButton("Назад", callback_data="Clerk|Back")]
    ]

    await update.callback_query.edit_message_text(
        text="Оберіть день: ",
        reply_markup=InlineKeyboardMarkup(kb)
    )



async def start_create_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Введіть домашнє завдання, яке хочете додати:")
    return HOMEWORK


async def get_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_homework"] = update.message.text

    kb = [
        [InlineKeyboardButton("Понеділок", callback_data="Clerk|monday")],
        [InlineKeyboardButton("Вівторок", callback_data="Clerk|tuesday")],
        [InlineKeyboardButton("Середа", callback_data="Clerk|wednesday")],
        [InlineKeyboardButton("Четвер", callback_data="Clerk|thursday")],
        [InlineKeyboardButton("П'ятниця", callback_data="Clerk|friday")]
    ]
    await update.message.reply_text(
        "Оберіть день:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return SUBJECT


async def create_homework_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Ключі точно як у JSON
    day_map = {
        "Clerk|monday": "monday",
        "Clerk|tuesday": "tuesday",
        "Clerk|wednesday": "wednesday",
        "Clerk|thursday": "thursday",
        "Clerk|friday": "friday"
    }
    
    day = day_map[q.data]  # англійський ключ
    context.user_data["day"] = day

    with open("hometask.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    lessons_list = data[day]  # отримуємо уроки

    # клавіатура предметів
    ckb = [[InlineKeyboardButton(lesson["предмет"], callback_data=f"homework3_{lesson['предмет']}")] for lesson in lessons_list]

    await q.message.edit_text(
        "Оберіть предмет:",
        reply_markup=InlineKeyboardMarkup(ckb)
    )
    return INPUT_HOMEWORK



async def create_homework_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    subject = q.data.replace("homework3_", "")
    context.user_data["subject"] = subject

    await q.message.reply_text("Введіть домашнє завдання для обраного предмету:")
    return INPUT_HOMEWORK


async def input_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data.get("day")
    subject = context.user_data.get("subject")
    new_homework = update.message.text
  
    with open("hometask.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for lesson in data[day]:
        if lesson["предмет"] == subject:
            lesson["д/з"] = new_homework
            break

    with open("hometask.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"Домашнє завдання для '{subject}' оновлено!")
    return ConversationHandler.END





if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    IS_password()

    conv_homework = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_homework, pattern="^Clerk\\|homework$")],
        states={
            HOMEWORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_homework)],
            SUBJECT: [CallbackQueryHandler(create_homework_2, pattern="^Clerk\\|")],
            INPUT_HOMEWORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_homework)]
        },
        fallbacks=[]
    )



    conv_registration = ConversationHandler(
        entry_points = [CallbackQueryHandler(on_registration_menu_pressed, pattern="^reg_")],
        states={
            REGISTRATION:[MessageHandler(filters.TEXT & ~filters.COMMAND, password)]
        },
        fallbacks=[],
    )


    app.add_handler(conv_registration)
    app.add_handler(conv_homework)  # Додавання ConversationHandler для ДЗ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registration", registration))
    app.add_handler(CallbackQueryHandler(on_registration_menu_pressed, pattern="^reg_"))
    app.add_handler(CallbackQueryHandler(Clic_Button, pattern="^(Student|Clerk)\|"))
    app.add_handler(CallbackQueryHandler(create_homework_3, pattern="^homework3_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, password))


    app.run_polling(drop_pending_updates=True)