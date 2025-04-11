from telebot import types
from Family.family_service import family_service
from BOT.keyboards import create_family_keyboard, create_main_keyboard, create_confirm_keyboard


def register_family_handlers(bot):
    def show_family_menu(chat_id, username):
        """Показывает меню семьи с клавиатурой"""
        bot.send_message(
            chat_id,
            "Меню семьи",
            reply_markup=create_family_keyboard(username)
        )

    @bot.message_handler(func=lambda msg: msg.text == "↩️ Назад")
    def handle_back(message):
        username = message.from_user.username
        # Изменено: теперь возвращаемся в главное меню вместо меню семьи
        bot.send_message(
            message.chat.id,
            "Главное меню",
            reply_markup=create_main_keyboard()
        )

    @bot.message_handler(func=lambda msg: msg.text == "➕ Создать")
    def handle_create_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if family_service.get_family_id(username):
            show_family_menu(chat_id, username)
            bot.send_message(chat_id, "Вы уже состоите в семье.")
            return

        back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_keyboard.add("↩️ Назад")

        msg = bot.send_message(chat_id, "Введите название вашей семьи:",
                               reply_markup=back_keyboard)
        bot.register_next_step_handler(msg, process_family_name)

    def process_family_name(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if message.text == '↩️ Назад':
            # Изменено: теперь возвращаемся в главное меню
            bot.send_message(chat_id, "Главное меню", reply_markup=create_main_keyboard())
            return

        family_name = message.text.strip()

        if not family_name:
            back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back_keyboard.add("↩️ Назад")

            msg = bot.send_message(chat_id, "Название не может быть пустым. Введите название:",
                                   reply_markup=back_keyboard)
            bot.register_next_step_handler(msg, process_family_name)
            return

        back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_keyboard.add("↩️ Назад")

        msg = bot.send_message(chat_id,
                               "Придумайте 6-значный код для присоединения к семье:",
                               reply_markup=back_keyboard)
        bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))

    def process_join_code(message, family_name, username):
        chat_id = message.chat.id

        if message.text == '↩️ Назад':
            # Изменено: теперь возвращаемся в главное меню
            bot.send_message(chat_id, "Главное меню", reply_markup=create_main_keyboard())
            return

        join_code = message.text.strip()

        if len(join_code) != 6:
            back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back_keyboard.add("↩️ Назад")

            msg = bot.send_message(chat_id, "Код должен быть ровно 6 символов. Попробуйте еще раз:",
                                   reply_markup=back_keyboard)
            bot.register_next_step_handler(msg, lambda m: process_join_code(m, family_name, username))
            return

        try:
            if family_service.create_family(family_name, join_code, username):
                show_family_menu(chat_id, username)
                bot.send_message(chat_id, f"✅ Семья '{family_name}' создана!\nКод: {join_code}")
            else:
                show_family_menu(chat_id, username)
                bot.send_message(chat_id, "❌ Не удалось создать семью.")
        except Exception as e:
            print(f"Ошибка: {e}")
            show_family_menu(chat_id, username)
            bot.send_message(chat_id, "❌ Произошла ошибка.")

    @bot.message_handler(func=lambda msg: msg.text == "🚪 Выйти")
    def handle_leave_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if not family_service.get_family_id(username):
            show_family_menu(chat_id, username)
            bot.send_message(chat_id, "Вы не состоите в семье.")
            return

        confirm_keyboard = create_confirm_keyboard()
        confirm_keyboard.add("↩️ Назад")

        bot.send_message(chat_id, "Вы уверены, что хотите выйти из семьи?",
                         reply_markup=confirm_keyboard)
        bot.register_next_step_handler(message, process_leave_confirmation)

    def process_leave_confirmation(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if message.text == '↩️ Назад':
            # Изменено: теперь возвращаемся в главное меню
            bot.send_message(chat_id, "Главное меню", reply_markup=create_main_keyboard())
            return

        if message.text == "Да":
            if family_service.leave_family(username):
                bot.send_message(chat_id, "✅ Вы успешно вышли из семьи.",
                             reply_markup=create_main_keyboard())
            else:
                bot.send_message(chat_id, "❌ Не удалось выйти из семьи.",
                             reply_markup=create_main_keyboard())
        else:
            bot.send_message(chat_id, "Отмена выхода из семьи.",
                             reply_markup=create_main_keyboard())

    @bot.message_handler(func=lambda msg: msg.text == "👪 Моя семья")
    def handle_family_info(message):
        chat_id = message.chat.id
        username = message.from_user.username

        family_id = family_service.get_family_id(username)
        if not family_id:
            show_family_menu(chat_id, username)
            bot.send_message(chat_id, "Вы пока не состоите в семье.")
            return

        family_info = family_service.get_family_info(family_id)
        if family_info:
            members = "\n".join([f"• @{user}" for user in family_service.get_family_members(family_id)])
            bot.send_message(chat_id,
                             f"👪 Семья: {family_info['family_name']}\n"
                             f"👤 Участников: {family_info['member_count']}\n"
                             f"🔸 Участники:\n{members}")
        else:
            bot.send_message(chat_id, "Не удалось получить информацию о семье.")

    @bot.message_handler(func=lambda msg: msg.text == "🔗 Присоединиться")
    def handle_join_family(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if family_service.get_family_id(username):
            show_family_menu(chat_id, username)
            bot.send_message(chat_id, "❌ Вы уже состоите в семье.")
            return

        cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_keyboard.add("❌ Отмена", "↩️ Назад")

        msg = bot.send_message(chat_id, "🔑 Введите 6-значный код присоединения:",
                               reply_markup=cancel_keyboard)
        bot.register_next_step_handler(msg, process_join_family_code)

    def process_join_family_code(message):
        chat_id = message.chat.id
        username = message.from_user.username

        if message.text == '↩️ Назад':
            # Изменено: теперь возвращаемся в главное меню
            bot.send_message(chat_id, "Главное меню", reply_markup=create_main_keyboard())
            return
        elif message.text == "❌ Отмена":
            bot.send_message(chat_id, "Отменено присоединение к семье.",
                             reply_markup=create_main_keyboard())
            return

        join_code = message.text.strip()
        if len(join_code) != 6:
            cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_keyboard.add("❌ Отмена", "↩️ Назад")

            msg = bot.send_message(chat_id, "❌ Код должен быть ровно 6 символов:",
                                   reply_markup=cancel_keyboard)
            bot.register_next_step_handler(msg, process_join_family_code)
            return

        try:
            if family_service.join_family(join_code, username):
                bot.send_message(chat_id, "✅ Вы успешно присоединились к семье!",
                             reply_markup=create_main_keyboard())
            else:
                cancel_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                cancel_keyboard.add("❌ Отмена", "↩️ Назад")

                msg = bot.send_message(chat_id, "❌ Неверный код. Попробуйте еще раз:",
                                       reply_markup=cancel_keyboard)
                bot.register_next_step_handler(msg, process_join_family_code)
        except Exception as e:
            print(f"Ошибка: {e}")
            bot.send_message(chat_id, "❌ Произошла ошибка.",
                             reply_markup=create_main_keyboard())