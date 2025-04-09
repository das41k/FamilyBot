# Family/family_handlers.py

from telebot import types

from Family.family_service import family_service
from BOT.keyboards import create_family_keyboard, create_main_keyboard, create_confirm_keyboard


def register_family_handlers(bot):

    @bot.message_handler(func=lambda msg: msg.text == "↩️ Назад")
    def handle_back(message):
        bot.send_message(
            message.chat.id,
            "🏠Главное меню",
            reply_markup=create_main_keyboard()
        )

    @bot.message_handler(func=lambda msg: msg.text == "➕ Создать")
    def handle_create_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if family_service.get_family_id(username):
            bot.send_message(chat_id, "Вы уже состоите в семье.",
                             reply_markup=create_family_keyboard(username))
            return

        msg = bot.send_message(chat_id, "Введите название вашей семьи:",
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_family_name)

    def process_family_name(message):
        chat_id = message.chat.id
        username = message.from_user.username
        family_name = message.text.strip()

        if not family_name:
            msg = bot.send_message(chat_id, "Название не может быть пустым. Введите название:")
            bot.register_next_step_handler(msg, process_family_name)
            return

        msg = bot.send_message(chat_id,
                               "Придумайте 6-значный код для присоединения к семье\n"
                               "(можно использовать цифры, буквы и символы):",
                               reply_markup=types.ReplyKeyboardRemove())

        bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))

    def process_join_code(message, family_name, username):
        chat_id = message.chat.id
        join_code = message.text.strip()

        if len(join_code) != 6:
            msg = bot.send_message(chat_id, "Код должен быть ровно 6 символов. Попробуйте еще раз:")
            bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))
            return

        if not family_service.check_join_code_available(join_code):
            msg = bot.send_message(chat_id,
                                   "❌ Этот код уже используется. Придумайте другой 6-значный код:",
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))
            return

        try:
            success = family_service.create_family(family_name, join_code, username)

            if success:
                bot.send_message(chat_id,
                                 f"✅ Семья '{family_name}' создана!\nКод для присоединения: {join_code}",
                                 reply_markup=create_family_keyboard(username))
            else:
                bot.send_message(chat_id,
                                 "❌ Не удалось создать семью. Возможно, имя уже занято.",
                                 reply_markup=create_family_keyboard(username))
        except Exception as e:
            print(f"Ошибка: {e}")
            bot.send_message(chat_id,
                             "❌ Произошла ошибка. Попробуйте позже.",
                             reply_markup=create_family_keyboard(username))

    @bot.message_handler(func=lambda msg: msg.text == "🚪 Выйти")
    def handle_leave_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if not family_service.get_family_id(username):
            bot.send_message(chat_id, "Вы не состоите в семье.",
                             reply_markup=create_family_keyboard(username))
            return

        bot.send_message(chat_id,
                         "Вы уверены, что хотите выйти из семьи?",
                         reply_markup=create_confirm_keyboard())

        bot.register_next_step_handler(message, process_leave_confirmation)

    def process_leave_confirmation(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if message.text.lower() == "да":
            success = family_service.leave_family(username)
            if success:
                bot.send_message(chat_id, "✅ Вы успешно вышли из семьи.",
                                 reply_markup=create_family_keyboard(username))
            else:
                bot.send_message(chat_id, "❌ Не удалось выйти из семьи.",
                                 reply_markup=create_family_keyboard(username))
        else:
            bot.send_message(chat_id, "Отмена выхода из семьи.",
                             reply_markup=create_family_keyboard(username))

    @bot.message_handler(func=lambda msg: msg.text == "👪 Моя семья")
    def handle_family_info(message):
        chat_id = message.chat.id
        username = message.from_user.username

        family_id = family_service.get_family_id(username)
        if not family_id:
            bot.send_message(chat_id, "Вы пока не состоите в семье.",
                             reply_markup=create_family_keyboard(username))
            return

        family_info = family_service.get_family_info(family_id)

        if not family_info:
            bot.send_message(chat_id, "Не удалось получить информацию о семье.",
                             reply_markup=create_family_keyboard(username))
            return

        family_members = family_service.get_family_members(family_id)

        info_message = (
                f"👪 *Информация о вашей семье:*\n"
                f"📛 Название: *{family_info['family_name']}*\n"
                f"👤 Участников: {family_info['member_count']}\n\n"
                f"🔸 Участники:\n" + "\n".join([f"• @{user}" for user in family_members])
        )

        bot.send_message(chat_id, info_message, parse_mode='MarkdownV2',
                         reply_markup=create_family_keyboard(username))

    @bot.message_handler(func=lambda msg: msg.text == "🔗 Присоединиться")
    def handle_join_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if family_service.get_family_id(username):
            bot.send_message(
                chat_id,
                "❌ Вы уже состоите в семье.",
                reply_markup=create_family_keyboard(username)
            )
            return

        # Создаем клавиатуру с кнопкой отмены
        cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_keyboard.add("❌ Отмена")

        msg = bot.send_message(
            chat_id,
            "🔑 Введите 6-значный код присоединения к семье:",
            reply_markup=cancel_keyboard
        )
        bot.register_next_step_handler(msg, process_join_family_code)

    def process_join_family_code(message):
        chat_id = message.chat.id
        username = message.from_user.username
        user_input = message.text.strip()

        # Обработка отмены
        if user_input == "❌ Отмена":
            bot.send_message(
                chat_id,
                "Отменено присоединение к семье.",
                reply_markup=create_family_keyboard(username)
            )
            return

        # Проверка длины кода
        if len(user_input) != 6:
            # Сохраняем клавиатуру с отменой
            cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_keyboard.add("❌ Отмена")

            msg = bot.send_message(
                chat_id,
                "❌ Код должен быть ровно 6 символов. Попробуйте еще раз или нажмите 'Отмена':",
                reply_markup=cancel_keyboard
            )
            bot.register_next_step_handler(msg, process_join_family_code)
            return

        try:
            success = family_service.join_family(user_input, username)

            if success:
                bot.send_message(
                    chat_id,
                    "✅ Вы успешно присоединились к семье!",
                    reply_markup=create_family_keyboard(username)
                )
            else:
                cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                cancel_keyboard.add("❌ Отмена")

                msg = bot.send_message(
                    chat_id,
                    "❌ Неверный код или семья не найдена. Попробуйте еще раз или нажмите 'Отмена':",
                    reply_markup=cancel_keyboard
                )
                bot.register_next_step_handler(msg, process_join_family_code)

        except Exception as e:
            print(f"Ошибка при присоединении: {e}")
            bot.send_message(
                chat_id,
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=create_family_keyboard(username)
            )

