import telebot
from telebot import types

from ServiceAndrey import Part_Andrey

bot = telebot.TeleBot('7594766898:AAGCf-erF5yZCHicKVydjky_kOoFDODOfAQ')

def create_main_keyboard(username):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if Part_Andrey.get_family_id(username):
        keyboard.add("Создать семью", "Выйти из семьи","Моя семья")
    else:
        keyboard.add("Создать семью")
    return keyboard

def create_confirm_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Да", "Нет")
    return keyboard

@bot.message_handler(commands=['start'])
def start_handler(message):
    username = message.from_user.username
    Part_Andrey.save_user_to_db(username)
    bot.send_message(message.chat.id, f"Привет, @{username}! Выберите действие:",
                     reply_markup=create_main_keyboard(username))

@bot.message_handler(func=lambda msg: msg.text == "Создать семью")
def handle_create_family(message):
    chat_id = message.chat.id
    username = message.from_user.username

    if Part_Andrey.get_family_id(username):
        bot.send_message(chat_id, "Вы уже состоите в семье.",
                         reply_markup=create_main_keyboard(username))
        return

    # Запрашиваем название семьи
    msg = bot.send_message(chat_id, "Введите название вашей семьи:",
                           reply_markup=types.ReplyKeyboardRemove())

    # Регистрируем следующий шаг
    bot.register_next_step_handler(msg, process_family_name)


def process_family_name(message):
    chat_id = message.chat.id
    username = message.from_user.username
    family_name = message.text.strip()

    if not family_name:
        msg = bot.send_message(chat_id, "Название не может быть пустым. Введите название:")
        bot.register_next_step_handler(msg, process_family_name)
        return

    # Запрашиваем код присоединения
    msg = bot.send_message(chat_id,
                           "Придумайте 6-значный код для присоединения к семье\n"
                           "(можно использовать цифры, буквы и символы):",
                           reply_markup=types.ReplyKeyboardRemove())

    bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))


def process_join_code(message, family_name, username):
    chat_id = message.chat.id
    join_code = message.text.strip()

    # Проверяем длину кода
    if len(join_code) != 6:
        msg = bot.send_message(chat_id, "Код должен быть ровно 6 символов. Попробуйте еще раз:")
        bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))
        return

    if not Part_Andrey.check_join_code_available(join_code):
        msg = bot.send_message(chat_id,
                               "❌ Этот код уже используется. Придумайте другой 6-значный код:",
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))
        return

    try:
        success = Part_Andrey.create_family(family_name, join_code, username)

        if success:
            bot.send_message(chat_id,
                             f"✅ Семья '{family_name}' создана!\nКод для присоединения: {join_code}",
                             reply_markup=create_main_keyboard(username))
        else:
            bot.send_message(chat_id,
                             "❌ Не удалось создать семью. Возможно, имя уже занято.",
                             reply_markup=create_main_keyboard(username))
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(chat_id,
                         "❌ Произошла ошибка. Попробуйте позже.",
                         reply_markup=create_main_keyboard(username))

@bot.message_handler(func=lambda msg: msg.text == "Выйти из семьи")
def handle_leave_family(message):
    chat_id = message.chat.id
    username = message.from_user.username

    if not Part_Andrey.get_family_id(username):
        bot.send_message(chat_id, "Вы не состоите в семье.",
                         reply_markup=create_main_keyboard(username))
        return

    # Запрашиваем подтверждение
    bot.send_message(chat_id,
                     "Вы уверены, что хотите выйти из семьи?",
                     reply_markup=create_confirm_keyboard())

    # Регистрируем следующий шаг
    bot.register_next_step_handler(message, process_leave_confirmation)


def process_leave_confirmation(message):
    chat_id = message.chat.id
    username = message.from_user.username

    if message.text.lower() == "да":
        success = Part_Andrey.leave_family(username)
        if success:
            bot.send_message(chat_id, "✅ Вы успешно вышли из семьи.",
                             reply_markup=create_main_keyboard(username))
        else:
            bot.send_message(chat_id, "❌ Не удалось выйти из семьи.",
                             reply_markup=create_main_keyboard(username))
    else:
        bot.send_message(chat_id, "Отмена выхода из семьи.",
                         reply_markup=create_main_keyboard(username))
@bot.message_handler(func=lambda msg: msg.text == "Моя семья")
def handle_family_info(message):
    chat_id = message.chat.id
    username = message.from_user.username

    family_id = Part_Andrey.get_family_id(username)
    if not family_id:
        bot.send_message(chat_id, "Вы пока не состоите в семье.", reply_markup=create_main_keyboard(username))
        return

    family_info = Part_Andrey.get_family_info(family_id)

    if not family_info:
        bot.send_message(chat_id, "Не удалось получить информацию о семье.",
                         reply_markup=create_main_keyboard(username))
        return

    family_members = Part_Andrey.get_family_members(family_id)

    info_message = (
            f"👪 *Информация о вашей семье:*\n"
            f"📛 Название: *{family_info['family_name']}*\n"
            f"👤 Участников: {family_info['member_count']}\n\n"
            f"🔸 Участники:\n" + "\n".join([f"• @{user}" for user in family_members])
    )

    bot.send_message(chat_id, info_message, parse_mode='MarkdownV2', reply_markup=create_main_keyboard(username))


@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    bot.send_message(message.chat.id,
                     "Пожалуйста, используйте кнопки меню.",
                     reply_markup=create_main_keyboard(message.from_user.username))


if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()