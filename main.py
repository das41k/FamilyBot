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


def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["Создать семью", "Присоединиться к семье", "Моя семья"]
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=['start'])
def start_handler(message):
    username = message.from_user.username
    ServiceAndrey.Part_Andrey.save_user_to_db(username)
    bot.send_message(message.chat.id, f"Привет, @{username}! Выберите действие:", reply_markup=create_main_keyboard())


@bot.message_handler(func=lambda msg: True, state=None)
def handle_menu_selection(message):
    chat_id = message.chat.id
    username = message.from_user.username
    user_msg_id = message.message_id

    if message.text not in ["Создать семью", "Присоединиться к семье", "Моя семья"]:
        fallback_handler(message)
        return

    # Обрабатываем выбор
    if message.text == "Создать семью":
        if Part_Andrey.get_family_id(username):
            bot.send_message(chat_id, "Вы уже состоите в семье.", reply_markup=create_main_keyboard())
            return

        bot.set_state(chat_id, MyStates.CREATE_FAMILY)
        bot_msg = bot.send_message(chat_id, "Введите название вашей семьи:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}

    elif message.text == "Присоединиться к семье":
        if Part_Andrey.get_family_id(username):
            bot.send_message(chat_id, "Вы уже состоите в семье.", reply_markup=create_main_keyboard())
            return

        bot.set_state(chat_id, MyStates.JOIN_FAMILY)
        bot_msg = bot.send_message(chat_id, "Введите код присоединения к семье:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}

    elif message.text == "Моя семья":
        handle_family_info(message)


# Обработка создания семьи
@bot.message_handler(state=MyStates.CREATE_FAMILY)
def process_family_name_step(message):
    chat_id = message.chat.id
    username = message.from_user.username
    family_name = message.text.strip()

    # Проверяем, не является ли ввод командой меню
    if family_name in ["Создать семью", "Присоединиться к семье", "Моя семья"]:
        bot.delete_state(chat_id)
        handle_menu_selection(message)
        return

    if not family_name:
        bot_msg = bot.send_message(chat_id, "Название семьи не может быть пустым. Повторите ввод:")
        user_last_prompt[chat_id] = {"user": message.message_id, "bot": bot_msg.message_id}
        return

    success = Part_Andrey.create_family(family_name, username)
    if success:
        bot.send_message(chat_id, f"✅ Семья '{family_name}' успешно создана!", reply_markup=create_main_keyboard())
    else:
        bot.send_message(chat_id, "❌ Не удалось создать семью. Попробуйте позже.", reply_markup=create_main_keyboard())

    bot.delete_state(chat_id)


# Обработка присоединения к семье
@bot.message_handler(state=MyStates.JOIN_FAMILY)
def process_join_family_step(message):
    chat_id = message.chat.id
    username = message.from_user.username
    join_code = message.text.strip()
    user_msg_id = message.message_id

    # Проверяем, не является ли ввод командой меню
    if join_code in ["Создать семью", "Присоединиться к семье", "Моя семья"]:
        bot.delete_state(chat_id)
        handle_menu_selection(message)
        return

    if not join_code or len(join_code) < 4:
        bot_msg = bot.send_message(chat_id, "Некорректный код. Попробуйте ещё раз:")
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}
        return

    success = Part_Andrey.join_family(join_code, username)
    if success:
        bot.send_message(chat_id, "✅ Вы успешно присоединились к семье!", reply_markup=create_main_keyboard())
    else:
        bot_msg = bot.send_message(chat_id, "❌ Код неверный или произошла ошибка. Повторите попытку:",
                                   reply_markup=create_main_keyboard())
        user_last_prompt[chat_id] = {"user": user_msg_id, "bot": bot_msg.message_id}
        return

    bot.delete_state(chat_id)


@bot.message_handler(func=lambda msg: msg.text == "Моя семья")
def handle_family_info(message):
    chat_id = message.chat.id
    username = message.from_user.username

    family_id = Part_Andrey.get_family_id(username)
    if not family_id:
        bot.send_message(chat_id, "Вы пока не состоите в семье.", reply_markup=create_main_keyboard())
        return

    family_info = Part_Andrey.get_family_info(family_id)

    if not family_info:
        bot.send_message(chat_id, "Не удалось получить информацию о семье.", reply_markup=create_main_keyboard())
        return

    family_members = Part_Andrey.get_family_members(family_id)

    info_message = (
            f"👪 *Информация о вашей семье:*\n"
            f"📛 Название: *{family_info['family_name']}*\n"
            f"👤 Участников: {family_info['member_count']}\n\n"
            f"🔸 Участники:\n" + "\n".join([f"• @{user}" for user in family_members])
    )

    bot.send_message(chat_id, info_message, parse_mode='MarkdownV2', reply_markup=create_main_keyboard())


@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    bot.send_message(message.chat.id, "Пожалуйста, выберите действие из меню.", reply_markup=create_main_keyboard())


bot.infinity_polling()