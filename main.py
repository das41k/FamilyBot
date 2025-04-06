import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

import ServiceAndrey
from ServiceAndrey import Part_Andrey

state_storage = StateMemoryStorage()
bot = telebot.TeleBot('7594766898:AAGCf-erF5yZCHicKVydjky_kOoFDODOfAQ', state_storage=state_storage)

# Глобальный словарь: chat_id -> {"user": msg_id, "bot": msg_id}
user_last_prompt = {}


class MyStates(StatesGroup):
    CREATE_FAMILY = State()
    JOIN_FAMILY = State()
    LEAVE_FAMILY = State()  # Добавляем состояние для выхода из семьи


def create_main_keyboard(username=None):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["Создать семью", "Присоединиться к семье", "Моя семья"]

    # Добавляем кнопку выхода только если пользователь в семье
    if username and Part_Andrey.get_family_id(username):
        buttons.append("Выйти из семьи")

    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=['start'])
def start_handler(message):
    username = message.from_user.username
    ServiceAndrey.Part_Andrey.save_user_to_db(username)
    bot.send_message(message.chat.id, f"Привет, @{username}! Выберите действие:",
                     reply_markup=create_main_keyboard(username))


@bot.message_handler(
    func=lambda msg: msg.text in ["Создать семью", "Присоединиться к семье", "Моя семья", "Выйти из семьи"], state=None)
def handle_menu_selection(message):
    chat_id = message.chat.id
    username = message.from_user.username
    user_msg_id = message.message_id

    # Удаляем старые сообщения
    if chat_id in user_last_prompt:
        ids = user_last_prompt[chat_id]
        for key in ["user", "bot"]:
            if key in ids:
                try:
                    bot.delete_message(chat_id, ids[key])
                except Exception as e:
                    print(f"Не удалось удалить сообщение {key}: {e}")
        user_last_prompt.pop(chat_id)

    if message.text == "Создать семью":
        if Part_Andrey.get_family_id(username):
            bot.send_message(chat_id, "Вы уже состоите в семье.", reply_markup=create_main_keyboard(username))
            return

        bot.set_state(chat_id, MyStates.CREATE_FAMILY)
        bot_msg = bot.send_message(chat_id, "Введите название вашей семьи:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}

    elif message.text == "Присоединиться к семье":
        if Part_Andrey.get_family_id(username):
            bot.send_message(chat_id, "Вы уже состоите в семье.", reply_markup=create_main_keyboard(username))
            return

        bot.set_state(chat_id, MyStates.JOIN_FAMILY)
        bot_msg = bot.send_message(chat_id, "Введите код присоединения к семье:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}

    elif message.text == "Моя семья":
        handle_family_info(message)

    elif message.text == "Выйти из семьи":
        handle_leave_family(message)


# Обработка создания семьи
@bot.message_handler(state=MyStates.CREATE_FAMILY)
def process_family_name_step(message):
    chat_id = message.chat.id
    username = message.from_user.username
    family_name = message.text.strip()

    # Удаляем предыдущие сообщения
    if chat_id in user_last_prompt:
        ids = user_last_prompt[chat_id]
        for key in ["user", "bot"]:
            if key in ids:
                try:
                    bot.delete_message(chat_id, ids[key])
                except Exception as e:
                    print(f"Ошибка удаления {key}: {e}")
        user_last_prompt.pop(chat_id)

    if not family_name:
        bot_msg = bot.send_message(chat_id, "Название семьи не может быть пустым. Повторите ввод:")
        user_last_prompt[chat_id] = {"user": message.message_id, "bot": bot_msg.message_id}
        return

    success = Part_Andrey.create_family(family_name, username)
    if success:
        bot.send_message(chat_id, f"✅ Семья '{family_name}' успешно создана!",
                         reply_markup=create_main_keyboard(username))
    else:
        bot.send_message(chat_id, "❌ Не удалось создать семью. Попробуйте позже.",
                         reply_markup=create_main_keyboard(username))

    bot.delete_state(chat_id)


# Обработка присоединения к семье
@bot.message_handler(state=MyStates.JOIN_FAMILY)
def process_join_family_step(message):
    chat_id = message.chat.id
    username = message.from_user.username
    join_code = message.text.strip()
    user_msg_id = message.message_id

    # Удаляем предыдущие сообщения
    if chat_id in user_last_prompt:
        ids = user_last_prompt[chat_id]
        for key in ["user", "bot"]:
            if key in ids:
                try:
                    bot.delete_message(chat_id, ids[key])
                except Exception as e:
                    print(f"Ошибка удаления {key}: {e}")
        user_last_prompt.pop(chat_id)

    if not join_code or len(join_code) < 4:
        bot_msg = bot.send_message(chat_id, "Некорректный код. Попробуйте ещё раз:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}
        return

    success = Part_Andrey.join_family(join_code, username)
    if success:
        bot.send_message(chat_id, "✅ Вы успешно присоединились к семье!",
                         reply_markup=create_main_keyboard(username))
    else:
        bot_msg = bot.send_message(chat_id, "❌ Код неверный или произошла ошибка. Повторите попытку:",
                                   reply_markup=create_main_keyboard(username))
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}
        return

    bot.delete_state(chat_id)


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


@bot.message_handler(func=lambda msg: msg.text == "Выйти из семьи")
def handle_leave_family(message):
    chat_id = message.chat.id
    username = message.from_user.username

    family_id = Part_Andrey.get_family_id(username)
    if not family_id:
        bot.send_message(chat_id, "Вы не состоите в семье.", reply_markup=create_main_keyboard(username))
        return

    # Создаем клавиатуру для подтверждения
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Да", "Нет")

    bot.set_state(chat_id, MyStates.LEAVE_FAMILY)
    bot_msg = bot.send_message(chat_id, "Вы уверены, что хотите выйти из семьи?", reply_markup=markup)
    user_last_prompt[chat_id] = {"user": message.message_id, "bot": bot_msg.message_id}


# Обработка подтверждения выхода из семьи
@bot.message_handler(state=MyStates.LEAVE_FAMILY)
def process_leave_family(message):
    chat_id = message.chat.id
    username = message.from_user.username

    # Удаляем предыдущие сообщения
    if chat_id in user_last_prompt:
        ids = user_last_prompt[chat_id]
        for key in ["user", "bot"]:
            if key in ids:
                try:
                    bot.delete_message(chat_id, ids[key])
                except Exception as e:
                    print(f"Ошибка удаления {key}: {e}")
        user_last_prompt.pop(chat_id)

    if message.text.lower() == "да":
        success = Part_Andrey.leave_family(username)
        if success:
            bot.send_message(chat_id, "✅ Вы успешно вышли из семьи.",
                             reply_markup=create_main_keyboard(username))
        else:
            bot.send_message(chat_id, "❌ Не удалось выйти из семьи. Попробуйте позже.",
                             reply_markup=create_main_keyboard(username))
    else:
        bot.send_message(chat_id, "Отмена выхода из семьи.",
                         reply_markup=create_main_keyboard(username))

    bot.delete_state(chat_id)

@bot.message_handler(func=lambda m: True, state=None)
def fallback_handler(message):
    username = message.from_user.username
    bot.send_message(message.chat.id, "Пожалуйста, выберите действие из меню.",
                     reply_markup=create_main_keyboard(username))


bot.infinity_polling()