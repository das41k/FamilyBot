import telebot
from telebot import types
import datetime
import DBconnection
import ServiceAndrey
from ServiceAndrey import Part_Andrey

user_data = {}

bot = telebot.TeleBot('7594766898:AAGCf-erF5yZCHicKVydjky_kOoFDODOfAQ')
# Создаем клавиатуру
def create_reply_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Добавить расходы",
        "Добавить постоянные расходы",
        "Добавить доходы",
        "Добавить постоянные доходы",
        "Показать статистику",
        "Установить лимиты",
        "Настроить уведомления",
        "Установить цели",
        "Создать семью",
        "Присоединиться к семье",
        "Сравнить с другими",
        "Достижения",
        "Черный список",
    ]
    keyboard.add(*buttons)
    return keyboard

# Edited here `15151216166161611661616161
# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    username = message.from_user.username
    ServiceAndrey.Part_Andrey.save_user_to_db(username)
    user_data[message.chat.id] = {'username': username}
    keyboard = create_reply_keyboard()
    bot.send_message(message.chat.id, f"Привет, @{username}! Чем могу помочь?", reply_markup=keyboard)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    username = message.from_user.username
    ServiceAndrey.Part_Andrey.save_user_to_db(username)
    user_data[message.chat.id] = {'username': username}
    if message.text == "Добавить расходы":

        operation_id = ServiceAndrey.Part_Andrey.get_operation_type_id_from_db("Расход")
        if not operation_id:
            bot.send_message(message.chat.id, "Ошибка: не удалось определить тип операции")
            return

        # Сохраняем operation_type_id для этого чата
        msg = bot.send_message(message.chat.id, "Введите сумму расхода (в рублях):")
        chat_id = msg.chat.id
        user_data[chat_id]['operation_type_id'] = operation_id
        user_data[chat_id]['operation_type'] = "Расход"
        bot.register_next_step_handler(msg, process_amount_step)

    elif message.text == "Создать семью":
        msg = bot.send_message(message.chat.id, "Введите название для вашей семьи:")
        bot.register_next_step_handler(msg, process_family_name_step)

    elif message.text == "Присоединиться к семье":
        if ServiceAndrey.Part_Andrey.get_family_id(username):
            bot.send_message(message.chat.id, "Вы уже состоите в семье")
        else:
            msg = bot.send_message(message.chat.id, "Введите код присоединения к семье:")
            bot.register_next_step_handler(msg, process_join_family_step)

    elif message.text == "Добавить постоянные расходы":

        operation_id = ServiceAndrey.Part_Andrey.get_operation_type_id_from_db("Расход")
        if not operation_id:
            bot.send_message(message.chat.id, "Ошибка: не удалось определить тип операции")
            return

        msg = bot.send_message(message.chat.id, "Введите сумму постоянного расхода (в рублях):")
        chat_id = msg.chat.id
        user_data[chat_id]['operation_type_id'] = operation_id
        user_data[chat_id]['operation_type'] = "Постоянный расход"
        user_data[chat_id]['is_recurring'] = True
        bot.register_next_step_handler(msg, process_recurring_amount_step)

    elif message.text == "Добавить доходы":

        operation_id = ServiceAndrey.Part_Andrey.get_operation_type_id_from_db("Доход")
        if not operation_id:
            bot.send_message(message.chat.id, "Ошибка: не удалось определить тип операции")
            return

        msg = bot.send_message(message.chat.id, "Введите сумму дохода (в рублях):")
        chat_id = msg.chat.id
        user_data[chat_id]['operation_type_id'] = operation_id
        user_data[chat_id]['operation_type'] = "Доход"
        bot.register_next_step_handler(msg, process_amount_step)

    elif message.text == "Добавить постоянные доходы":

        operation_id = ServiceAndrey.Part_Andrey.get_operation_type_id_from_db("Доход")
        if not operation_id:
            bot.send_message(message.chat.id, "Ошибка: не удалось определить тип операции")
            return

        msg = bot.send_message(message.chat.id, "Введите сумму постоянного дохода (в рублях):")
        chat_id = msg.chat.id
        user_data[chat_id]['operation_type_id'] = operation_id
        user_data[chat_id]['operation_type'] = "Постоянный доход"
        user_data[chat_id]['is_recurring'] = True
        bot.register_next_step_handler(msg, process_recurring_amount_step)

    elif message.text == "Показать статистику":
        bot.send_message(message.chat.id, "Выберите тип статистики: по типам расходов, по пользователям или за определенный период.")
    elif message.text == "Установить лимиты":
        bot.send_message(message.chat.id, "Введите категорию и лимит расходов.")
    elif message.text == "Настроить уведомления":
        bot.send_message(message.chat.id, "Выберите тип уведомлений: напоминания, превышение лимита и т.д.")
    elif message.text == "Установить цели":
        bot.send_message(message.chat.id, "Введите цель и сумму для накопления.")
    elif message.text == "Сравнить с другими":
        bot.send_message(message.chat.id, "Сравнение финансов с другими пользователями.")
    elif message.text == "Достижения":
        bot.send_message(message.chat.id, "Ваши финансовые достижения.")
    elif message.text == "Черный список":
        bot.send_message(message.chat.id, "Добавьте категории для ограничения трат.")
    elif message.text == "Постоянные доходы/расходы":
        bot.send_message(message.chat.id, "Настройте постоянные доходы и расходы.")
    else:
        bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите из меню.")

def create_categories_keyboard():
    categories = ServiceAndrey.Part_Andrey.get_categories_from_db()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    keyboard.add(*categories.keys())
    return keyboard

def process_amount_step(message):
    try:
        chat_id = message.chat.id
        amount = float(message.text)
        user_data[chat_id]['amount'] = amount

        # Для доходов сразу запрашиваем дату (без категории)
        if user_data[chat_id]['operation_type'] == "Доход":
            msg = bot.send_message(chat_id, "Введите дату дохода в формате ГГГГ-ММ-ДД:")
            bot.register_next_step_handler(msg, process_date_step)
        else:
            # Для расходов показываем категории
            msg = bot.send_message(chat_id, "Выберите категорию расхода:",
                                   reply_markup=create_categories_keyboard())
            bot.register_next_step_handler(msg, process_category_step)

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму (число).",
                         reply_markup=create_reply_keyboard())


def process_category_step(message):
    chat_id = message.chat.id
    categories = ServiceAndrey.Part_Andrey.get_categories_from_db()

    if message.text not in categories:
        msg = bot.send_message(chat_id, "Пожалуйста, выберите категорию из предложенных:",
                               reply_markup=create_categories_keyboard())
        bot.register_next_step_handler(msg, process_category_step)
        return

    # Сохраняем категорию
    user_data[chat_id]['category_id'] = categories[message.text]

    # Запрашиваем дату (возвращаем основную клавиатуру)
    msg = bot.send_message(chat_id, "Введите дату расхода в формате ГГГГ-ММ-ДД (например, 2023-10-05):",
                           reply_markup=create_reply_keyboard())
    bot.register_next_step_handler(msg, process_date_step)


def process_date_step(message):
    try:
        chat_id = message.chat.id
        user_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        timestamp = datetime.datetime.combine(user_date, datetime.datetime.min.time())

        username = user_data[chat_id]['username']
        client_id = ServiceAndrey.Part_Andrey.get_client_id(username)

        if not client_id:
            bot.send_message(chat_id, "Ошибка: пользователь не найден")
            return

        family_id = ServiceAndrey.Part_Andrey.get_family_id(username)

        # Получаем сохраненные данные
        amount = user_data[chat_id]['amount']
        operation_type_id = user_data[chat_id]['operation_type_id']

        category_id = user_data[chat_id].get('category_id')

        # Вызываем метод добавления доходов/расходов
        ServiceAndrey.Part_Andrey.add_operation(amount, timestamp,
                                               category_id, operation_type_id,
                                               client_id, family_id)

        # Формируем сообщение об успешном добавлении
        operation_type = user_data[chat_id]['operation_type']
        if operation_type == "Расход":
            categories = ServiceAndrey.Part_Andrey.get_categories_from_db()
            category_name = [name for name, id_ in categories.items() if id_ == category_id][0]
            msg = f"{operation_type} на сумму {amount} руб. в категории '{category_name}' на дату {user_date}"
        else:
            msg = f"{operation_type} на сумму {amount} руб. на дату {user_date}"

        bot.send_message(chat_id, f"{msg} успешно добавлен!")

        # Очищаем временные данные
        if chat_id in user_data:
            del user_data[chat_id]
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД.")


def process_family_name_step(message):
    try:
        chat_id = message.chat.id
        family_name = message.text.strip()

        if len(family_name) < 3:
            bot.send_message(chat_id, "Название семьи должно содержать минимум 3 символа."
                                      " Попробуйте еще раз:")
            bot.register_next_step_handler(message, process_family_name_step)
            return

        # Генерируем уникальный код для присоединения
        msg = bot.send_message(chat_id, "Придумайте код для присоединения к семье (минимум 6 символов):")
        user_data[chat_id]['family_name'] = family_name
        bot.register_next_step_handler(msg, process_join_code_step)

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")


def process_join_code_step(message):
    try:
        chat_id = message.chat.id
        join_code = message.text.strip()

        if len(join_code) < 6:
            bot.send_message(chat_id, "Код должен содержать минимум 6 символов. Попробуйте еще раз:")
            bot.register_next_step_handler(message, process_join_code_step)
            return

        # Создаем семью с пользовательским кодом
        family_id = ServiceAndrey.Part_Andrey.create_family(
            family_name=user_data[chat_id]['family_name'],
            join_code=join_code,
            creator_username=user_data[chat_id]['username']
        )

        if family_id:
            bot.send_message(chat_id, f"Семья '{user_data[chat_id]['family_name']}' успешно создана!\n"
                                      f"Код для присоединения: {join_code}\n"
                                      "Дайте этот код другим членам семьи для присоединения.")
        else:
            bot.send_message(chat_id, "Не удалось создать семью. Попробуйте позже.")

        # Очищаем временные данные
        if 'family_name' in user_data[chat_id]:
            del user_data[chat_id]['family_name']

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")


def process_join_family_step(message):
    try:
        chat_id = message.chat.id
        join_code = message.text.strip()
        username = user_data[chat_id]['username']

        if ServiceAndrey.Part_Andrey.join_family(join_code, username):
            bot.send_message(chat_id, "Вы успешно присоединились к семье!")
        else:
            bot.send_message(chat_id, "Неверный код присоединения или произошла ошибка")

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")


def process_recurring_amount_step(message):
    try:
        chat_id = message.chat.id
        amount = float(message.text)
        user_data[chat_id]['amount'] = amount

        if user_data[chat_id]['operation_type'] == "Постоянный расход":
            msg = bot.send_message(chat_id, "Выберите категорию расхода:",
                                   reply_markup=create_categories_keyboard())
            bot.register_next_step_handler(msg, process_recurring_category_step)
        else:
            msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):")
            bot.register_next_step_handler(msg, process_recurring_start_date_step)

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму (число).",
                         reply_markup=create_reply_keyboard())


def process_recurring_category_step(message):
    chat_id = message.chat.id
    categories = ServiceAndrey.Part_Andrey.get_categories_from_db()

    if message.text not in categories:
        msg = bot.send_message(chat_id, "Пожалуйста, выберите категорию из предложенных:",
                               reply_markup=create_categories_keyboard())
        bot.register_next_step_handler(msg, process_recurring_category_step)
        return

    user_data[chat_id]['category_id'] = categories[message.text]

    msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(msg, process_recurring_start_date_step)


def process_recurring_start_date_step(message):
    try:
        chat_id = message.chat.id
        start_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        user_data[chat_id]['start_date'] = start_date

        msg = bot.send_message(chat_id, "Введите дату окончания (ГГГГ-ММ-ДД):")
        bot.register_next_step_handler(msg, process_recurring_end_date_step)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД.",
                         reply_markup=create_reply_keyboard())


def process_recurring_end_date_step(message):
    try:
        chat_id = message.chat.id
        end_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        start_date = user_data[chat_id]['start_date']

        # Проверка что дата окончания после даты начала
        if end_date <= start_date:
            bot.send_message(chat_id,
                             "Дата окончания должна быть после даты начала. Введите корректную дату (ГГГГ-ММ-ДД):",
                             reply_markup=create_reply_keyboard())
            bot.register_next_step_handler(message, process_recurring_end_date_step)
            return

        user_data[chat_id]['end_date'] = end_date

        # Создаем клавиатуру с интервалами
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = ["Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно"]
        keyboard.add(*buttons)

        msg = bot.send_message(chat_id, "Выберите интервал:", reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_recurring_interval_step)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД.",
                         reply_markup=create_reply_keyboard())


def process_recurring_interval_step(message):
    try:
        chat_id = message.chat.id
        interval_map = {
            "Ежедневно": "1 day",
            "Еженедельно": "1 week",
            "Ежемесячно": "1 month",
            "Ежегодно": "1 year"
        }

        if message.text not in interval_map:
            raise ValueError("Неверный интервал")

        payment_interval = interval_map[message.text]
        start_date = user_data[chat_id]['start_date']
        end_date = user_data[chat_id]['end_date']

        # Проверка минимального периода для интервала
        delta = end_date - start_date
        min_days = {
            "1 day": 1,
            "1 week": 7,
            "1 month": 28,
            "1 year": 365
        }[payment_interval]

        if delta.days < min_days:
            bot.send_message(chat_id,
                             f"Для интервала '{message.text}' период должен быть не менее {min_days} дней. "
                             "Пожалуйста, выберите другой интервал или измените даты.", reply_markup=create_reply_keyboard())
            return

        user_data[chat_id]['payment_interval'] = payment_interval

        # Получаем все необходимые данные
        username = user_data[chat_id]['username']
        client_id = ServiceAndrey.Part_Andrey.get_client_id(username)
        family_id = ServiceAndrey.Part_Andrey.get_family_id(username)

        if not client_id:
            bot.send_message(chat_id, "Ошибка: пользователь не найден")
            return

        amount = user_data[chat_id]['amount']
        operation_type_id = user_data[chat_id]['operation_type_id']
        start_date = user_data[chat_id]['start_date']
        end_date = user_data[chat_id]['end_date']

        # Для расходов получаем category_id, для доходов может быть None
        category_id = user_data[chat_id].get('category_id')

        # Добавляем постоянную операцию
        ServiceAndrey.Part_Andrey.add_recurring_operation(
            amount=amount,
            operation_type_id=operation_type_id,
            category_id=category_id,
            client_id=client_id,
            family_id=family_id,
            date_start=start_date,
            date_end=end_date,
            payment_interval=payment_interval
        )

        operation_type = user_data[chat_id]['operation_type']
        if operation_type == "Постоянный расход":
            categories = ServiceAndrey.Part_Andrey.get_categories_from_db()
            category_name = [name for name, id_ in categories.items() if id_ == category_id][0]
            msg = f"{operation_type} на сумму {amount} руб. в категории '{category_name}'"
        else:
            msg = f"{operation_type} на сумму {amount} руб."

        bot.send_message(chat_id,
                         f"{msg} с {start_date} по {end_date} ({payment_interval}) успешно добавлен!",
                         reply_markup=create_reply_keyboard())

        # Очищаем временные данные
        if chat_id in user_data:
            del user_data[chat_id]

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, выберите интервал из предложенных.",
                         reply_markup=create_reply_keyboard())
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")

# Запуск бота
bot.infinity_polling()