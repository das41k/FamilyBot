import datetime
from telebot import types
from BOT.keyboards import *
from Finance.finance_service import FinanceService

# Глобальный словарь для временного хранения данных пользователя
user_data = {}


def register_finance_handlers(bot):
    # Вспомогательные функции
    def return_to_finance_menu(chat_id):
        """Возвращает пользователя в меню финансов и очищает временные данные"""
        if chat_id in user_data:
            del user_data[chat_id]
        bot.send_message(chat_id, "Возвращаемся в меню Финансы",
                         reply_markup=create_finance())

    def create_back_keyboard():
        """Создает клавиатуру с кнопкой 'Назад'"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('❌ Отмена'))
        return keyboard

    # Обработчики команд
    @bot.message_handler(func=lambda msg: msg.text == "💸 Добавить расход")
    def handle_add_expense(message):
        chat_id = message.chat.id
        username = message.from_user.username

        operation_id = FinanceService.get_operation_type_id_from_db("Расход")
        if not operation_id:
            bot.send_message(chat_id, "Ошибка: не удалось определить тип операции")
            return

        user_data[chat_id] = {
            "username": username,
            "operation_type": "Расход",
            "operation_type_id": operation_id
        }

        msg = bot.send_message(chat_id, "Введите сумму расхода (в рублях):",
                               reply_markup=create_back_keyboard())
        bot.register_next_step_handler(msg, process_amount_step)

    def process_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            user_data[chat_id]['amount'] = amount

            keyboard = create_categories_keyboard()
            keyboard.add('❌ Отмена')
            msg = bot.send_message(chat_id, "Выберите категорию:",
                                   reply_markup=keyboard)
            bot.register_next_step_handler(msg, process_category_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Введите корректную сумму:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_amount_step)

    def process_category_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        categories = FinanceService.get_categories_from_db()

        if message.text not in categories:
            keyboard = create_categories_keyboard()
            keyboard.add('❌ Отмена')
            msg = bot.send_message(chat_id, "Выберите категорию из предложенных:",
                                   reply_markup=keyboard)
            bot.register_next_step_handler(msg, process_category_step)
            return

        user_data[chat_id]['category_id'] = categories[message.text]

        msg = bot.send_message(chat_id, "Введите дату в формате ГГГГ-ММ-ДД:",
                               reply_markup=create_back_keyboard())
        bot.register_next_step_handler(msg, process_date_step)

    def process_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            username = user_data[chat_id]['username']
            user_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            timestamp = datetime.datetime.combine(user_date, datetime.datetime.min.time())
            client_id = FinanceService.get_client_id(username)
            family_id = FinanceService.get_family_id(username)

            amount = user_data[chat_id]['amount']
            category_id = user_data[chat_id]['category_id']
            operation_type_id = user_data[chat_id]['operation_type_id']

            FinanceService.add_operation(
                amount,
                timestamp,
                category_id,
                operation_type_id,
                client_id,
                family_id
            )

            bot.send_message(chat_id, f"✅ Расход успешно добавлен!",
                             reply_markup=create_main_keyboard())
            del user_data[chat_id]

        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Повторите:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_date_step)

    @bot.message_handler(func=lambda msg: msg.text == "💰 Добавить доход")
    def handle_add_income(message):
        chat_id = message.chat.id
        username = message.from_user.username

        operation_id = FinanceService.get_operation_type_id_from_db("Доход")
        if not operation_id:
            bot.send_message(chat_id, "Ошибка: не удалось определить тип операции")
            return

        user_data[chat_id] = {
            "username": username,
            "operation_type": "Доход",
            "operation_type_id": operation_id
        }

        msg = bot.send_message(chat_id, "Введите сумму дохода (в рублях):",
                               reply_markup=create_back_keyboard())
        bot.register_next_step_handler(msg, process_income_amount_step)

    def process_income_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            user_data[chat_id]['amount'] = amount

            msg = bot.send_message(chat_id, "Введите дату дохода в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_income_date_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Введите корректную сумму:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_income_amount_step)

    def process_income_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            timestamp = datetime.datetime.combine(date, datetime.datetime.min.time())
            username = user_data[chat_id]['username']
            client_id = FinanceService.get_client_id(username)
            family_id = FinanceService.get_family_id(username)

            amount = user_data[chat_id]['amount']
            operation_type_id = user_data[chat_id]['operation_type_id']

            FinanceService.add_operation(
                amount,
                timestamp,
                None,  # Доходы без категории
                operation_type_id,
                client_id,
                family_id
            )

            bot.send_message(chat_id, "✅ Доход успешно добавлен!",
                             reply_markup=create_main_keyboard())
            del user_data[chat_id]

        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Повторите:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_income_date_step)

    @bot.message_handler(func=lambda msg: msg.text == "🔄 Постоянный расход")
    def handle_recurring_expense(message):
        start_recurring_flow(message, "Расход")

    @bot.message_handler(func=lambda msg: msg.text == "🔄 Постоянный доход")
    def handle_recurring_income(message):
        start_recurring_flow(message, "Доход")

    def start_recurring_flow(message, operation_type):
        chat_id = message.chat.id
        username = message.from_user.username

        operation_id = FinanceService.get_operation_type_id_from_db(operation_type)
        if not operation_id:
            bot.send_message(chat_id, "Ошибка: не удалось определить тип операции")
            return

        user_data[chat_id] = {
            "username": username,
            "operation_type": operation_type,
            "operation_type_id": operation_id
        }

        msg = bot.send_message(chat_id, "Введите сумму (в рублях):",
                               reply_markup=create_back_keyboard())
        bot.register_next_step_handler(msg, process_recurring_amount_step)

    def process_recurring_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            user_data[chat_id]['amount'] = amount

            if user_data[chat_id]['operation_type'] == "Расход":
                keyboard = create_categories_keyboard()
                keyboard.add('❌ Отмена')
                msg = bot.send_message(chat_id, "Выберите категорию расхода:",
                                       reply_markup=keyboard)
                bot.register_next_step_handler(msg, process_recurring_category_step)
            else:
                msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):",
                                       reply_markup=create_back_keyboard())
                bot.register_next_step_handler(msg, process_recurring_start_date_step)

        except ValueError:
            msg = bot.send_message(chat_id, "Пожалуйста, введите корректную сумму:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_recurring_amount_step)

    def process_recurring_category_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        categories = FinanceService.get_categories_from_db()

        if message.text not in categories:
            keyboard = create_categories_keyboard()
            keyboard.add('❌ Отмена')
            msg = bot.send_message(chat_id, "Выберите категорию из предложенных:",
                                   reply_markup=keyboard)
            bot.register_next_step_handler(msg, process_recurring_category_step)
            return

        user_data[chat_id]['category_id'] = categories[message.text]
        msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):",
                               reply_markup=create_back_keyboard())
        bot.register_next_step_handler(msg, process_recurring_start_date_step)

    def process_recurring_start_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            start_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            user_data[chat_id]['start_date'] = start_date

            msg = bot.send_message(chat_id, "Введите дату окончания (ГГГГ-ММ-ДД):",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_recurring_end_date_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Повторите:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_recurring_start_date_step)

    def process_recurring_end_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            end_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            start_date = user_data[chat_id]['start_date']

            if end_date <= start_date:
                msg = bot.send_message(chat_id, "Дата окончания должна быть позже даты начала:",
                                       reply_markup=create_back_keyboard())
                bot.register_next_step_handler(msg, process_recurring_end_date_step)
                return

            user_data[chat_id]['end_date'] = end_date

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно", "❌ Отмена")

            msg = bot.send_message(chat_id, "Выберите интервал:", reply_markup=keyboard)
            bot.register_next_step_handler(msg, process_recurring_interval_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Повторите:",
                                   reply_markup=create_back_keyboard())
            bot.register_next_step_handler(msg, process_recurring_end_date_step)

    def process_recurring_interval_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            interval_map = {
                "Ежедневно": "1 day",
                "Еженедельно": "1 week",
                "Ежемесячно": "1 month",
                "Ежегодно": "1 year"
            }

            if message.text not in interval_map:
                raise ValueError()

            interval = interval_map[message.text]
            delta = user_data[chat_id]['end_date'] - user_data[chat_id]['start_date']

            min_days = {
                "1 day": 1,
                "1 week": 7,
                "1 month": 28,
                "1 year": 365
            }[interval]

            if delta.days < min_days:
                bot.send_message(chat_id, f"Минимальный период для '{message.text}' — {min_days} дней.",
                                 reply_markup=create_back_keyboard())
                return

            user_data[chat_id]['payment_interval'] = interval

            username = user_data[chat_id]['username']
            client_id = FinanceService.get_client_id(username)
            family_id = FinanceService.get_family_id(username)

            FinanceService.add_recurring_operation(
                amount=user_data[chat_id]['amount'],
                operation_type_id=user_data[chat_id]['operation_type_id'],
                category_id=user_data[chat_id].get('category_id'),
                client_id=client_id,
                family_id=family_id,
                date_start=user_data[chat_id]['start_date'],
                date_end=user_data[chat_id]['end_date'],
                payment_interval=interval
            )

            bot.send_message(chat_id, "✅ Постоянная операция успешно добавлена!",
                             reply_markup=create_main_keyboard())
            del user_data[chat_id]

        except ValueError:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно", "❌ Отмена")
            msg = bot.send_message(chat_id, "Выберите интервал из предложенных:",
                                   reply_markup=keyboard)
            bot.register_next_step_handler(msg, process_recurring_interval_step)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка: {str(e)}",
                             reply_markup=create_back_keyboard())

    @bot.message_handler(func=lambda m: True)
    def fallback_handler(message):
        bot.send_message(
            message.chat.id,
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=create_main_keyboard()
        )