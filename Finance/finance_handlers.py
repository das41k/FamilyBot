import datetime
from telebot import types
from BOT.keyboards import *
from Finance.finance_service import FinanceService

# Глобальный словарь для временного хранения данных пользователя
user_data = {}


def create_categories_with_back():
    """Создает клавиатуру с категориями и кнопкой 'Отмена' без дублирования"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Получаем категории из базы данных
    categories = FinanceService.get_categories_from_db()

    # Добавляем кнопки категорий
    if categories:
        keyboard.add(*categories.keys())

    # Проверяем, есть ли уже кнопка "Отмена" в клавиатуре
    has_cancel = any(btn.text == "❌ Отмена" for row in keyboard.keyboard for btn in row)

    # Добавляем кнопку "Отмена", если её ещё нет
    if not has_cancel:
        keyboard.add("❌ Отмена")

    return keyboard


def register_finance_handlers(bot):
    # Вспомогательные функции клавиатур
    def create_finance_keyboard():
        """Основное меню финансов"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            "💸 Добавить расход",
            "💰 Добавить доход",
            "🔄 Постоянный расход",
            "🔄 Постоянный доход",
            "📊 Статистика",
            "🔙 Назад"
        ]
        keyboard.add(*buttons)
        return keyboard

    def create_back_only_keyboard():
        """Только кнопка Отмена"""
        return types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Отмена")

    def create_categories_keyboard():
        """Категории с одной кнопкой Отмена"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        categories = FinanceService.get_categories_from_db().keys()
        keyboard.add(*categories)
        keyboard.add("❌ Отмена")
        return keyboard

    def create_add_more_options():
        """Опции добавления + Отмена"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add("➕ Добавить еще категорию", "✅ Завершить", "❌ Отмена")
        return keyboard

    def create_interval_options():
        """Опции интервалов + Отмена"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add("Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно", "❌ Отмена")
        return keyboard

    def cleanup_user_data(chat_id):
        """Очистка временных данных"""
        if chat_id in user_data:
            del user_data[chat_id]

    def return_to_finance_menu(chat_id):
        """Возврат в меню финансов"""
        cleanup_user_data(chat_id)
        bot.send_message(chat_id, "Возвращаемся в меню Финансы",
                         reply_markup=create_finance_keyboard())

    # Обработчики расходов
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
            "operation_type_id": operation_id,
            "categories": []
        }

        msg = bot.send_message(chat_id, "Введите сумму расхода для первой категории (в рублях):",
                               reply_markup=create_back_only_keyboard())
        bot.register_next_step_handler(msg, process_expense_amount_step)

    def process_expense_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError()

            user_data[chat_id]['current_amount'] = amount

            msg = bot.send_message(chat_id, "Выберите категорию для этой суммы:",
                                   reply_markup=create_categories_keyboard())
            bot.register_next_step_handler(msg, process_expense_category_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Пожалуйста, введите корректную положительную сумму:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_expense_amount_step)

    def process_expense_category_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        categories = FinanceService.get_categories_from_db()

        if message.text not in categories:
            msg = bot.send_message(chat_id, "Выберите категорию из предложенных:",
                                   reply_markup=create_categories_keyboard())
            bot.register_next_step_handler(msg, process_expense_category_step)
            return

        user_data[chat_id]['categories'].append({
            'category_id': categories[message.text],
            'amount': user_data[chat_id]['current_amount']
        })

        report = "Вы добавили:\n" + "\n".join(
            f"- {FinanceService.get_category_name_by_id(item['category_id'])}: {item['amount']} руб."
            for item in user_data[chat_id]['categories']
        )
        total = sum(item['amount'] for item in user_data[chat_id]['categories'])
        report += f"\n\nОбщая сумма: {total} руб.\n\nХотите добавить еще категории?"

        msg = bot.send_message(chat_id, report,
                               reply_markup=create_add_more_options())
        bot.register_next_step_handler(msg, process_expense_add_more_step)

    def process_expense_add_more_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        if message.text == '✅ Завершить':
            if not user_data[chat_id]['categories']:
                msg = bot.send_message(chat_id, "Вы не добавили ни одной категории. Пожалуйста, выберите категорию:",
                                       reply_markup=create_categories_keyboard())
                bot.register_next_step_handler(msg, process_expense_category_step)
                return

            msg = bot.send_message(chat_id, "Введите дату расхода в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_expense_date_step)
            return

        if message.text == '➕ Добавить еще категорию':
            msg = bot.send_message(chat_id, "Введите сумму для следующей категории (в рублях):",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_expense_amount_step)
            return

        msg = bot.send_message(chat_id, "Пожалуйста, используйте кнопки меню:",
                               reply_markup=create_add_more_options())
        bot.register_next_step_handler(msg, process_expense_add_more_step)

    def process_expense_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            username = user_data[chat_id]['username']
            operation_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            timestamp = datetime.datetime.combine(operation_date, datetime.datetime.min.time())

            client_id = FinanceService.get_client_id(username)
            family_id = FinanceService.get_family_id(username)
            operation_type_id = user_data[chat_id]['operation_type_id']

            for category in user_data[chat_id]['categories']:
                FinanceService.add_operation(
                    amount=category['amount'],
                    operation_date=timestamp,
                    category_id=category['category_id'],
                    operation_type_id=operation_type_id,
                    client_id=client_id,
                    family_id=family_id
                )

            report = "✅ Расходы успешно добавлены!\n\n" + "\n".join(
                f"- {FinanceService.get_category_name_by_id(item['category_id'])}: {item['amount']} руб."
                for item in user_data[chat_id]['categories']
            )
            total = sum(item['amount'] for item in user_data[chat_id]['categories'])
            report += f"\n\nОбщая сумма: {total} руб."

            bot.send_message(chat_id, report,
                             reply_markup=create_main_keyboard())
            cleanup_user_data(chat_id)

        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_expense_date_step)



    # Обработчики доходов
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
                               reply_markup=create_back_only_keyboard())
        bot.register_next_step_handler(msg, process_income_amount_step)

    def process_income_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError()

            user_data[chat_id]['amount'] = amount

            msg = bot.send_message(chat_id, "Введите дату дохода в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_income_date_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Пожалуйста, введите корректную сумму:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_income_amount_step)

    def process_income_date_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            username = user_data[chat_id]['username']
            operation_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
            timestamp = datetime.datetime.combine(operation_date, datetime.datetime.min.time())

            client_id = FinanceService.get_client_id(username)
            family_id = FinanceService.get_family_id(username)

            FinanceService.add_operation(
                amount=user_data[chat_id]['amount'],
                timestamp=timestamp,
                category_id=None,
                operation_type_id=user_data[chat_id]['operation_type_id'],
                client_id=client_id,
                family_id=family_id
            )

            bot.send_message(chat_id, f"✅ Доход {user_data[chat_id]['amount']} руб. успешно добавлен!",
                             reply_markup=create_main_keyboard())
            cleanup_user_data(chat_id)

        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_income_date_step)

    # Обработчики постоянных операций
    @bot.message_handler(func=lambda msg: msg.text.startswith("🔄 Постоянный"))
    def handle_recurring_operation(message):
        chat_id = message.chat.id
        username = message.from_user.username
        is_expense = "расход" in message.text.lower()

        operation_type = "Расход" if is_expense else "Доход"
        operation_id = FinanceService.get_operation_type_id_from_db(operation_type)
        if not operation_id:
            bot.send_message(chat_id, "Ошибка: не удалось определить тип операции")
            return

        user_data[chat_id] = {
            "username": username,
            "operation_type": operation_type,
            "operation_type_id": operation_id,
            "is_expense": is_expense
        }

        msg = bot.send_message(chat_id, f"Введите сумму постоянного {operation_type.lower()}а (в рублях):",
                               reply_markup=create_back_only_keyboard())
        bot.register_next_step_handler(msg, process_recurring_amount_step)

    def process_recurring_amount_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError()

            user_data[chat_id]['amount'] = amount

            if user_data[chat_id]['is_expense']:
                msg = bot.send_message(chat_id, "Выберите категорию:",
                                       reply_markup=create_categories_with_back())
                bot.register_next_step_handler(msg, process_recurring_category_step)
            else:
                msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):",
                                       reply_markup=create_back_only_keyboard())
                bot.register_next_step_handler(msg, process_recurring_start_date_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Пожалуйста, введите корректную сумму:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_recurring_amount_step)

    def process_recurring_category_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        categories = FinanceService.get_categories_from_db()

        if message.text not in categories:
            msg = bot.send_message(chat_id, "Выберите категорию из предложенных:",
                                   reply_markup=create_categories_with_back())
            bot.register_next_step_handler(msg, process_recurring_category_step)
            return

        user_data[chat_id]['category_id'] = categories[message.text]
        msg = bot.send_message(chat_id, "Введите дату начала (ГГГГ-ММ-ДД):",
                               reply_markup=create_back_only_keyboard())
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
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_recurring_end_date_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
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
                msg = bot.send_message(chat_id, "Дата окончания должна быть позже даты начала. Повторите ввод:",
                                       reply_markup=create_back_only_keyboard())
                bot.register_next_step_handler(msg, process_recurring_end_date_step)
                return

            user_data[chat_id]['end_date'] = end_date
            msg = bot.send_message(chat_id, "Выберите интервал:",
                                   reply_markup=create_interval_options())
            bot.register_next_step_handler(msg, process_recurring_interval_step)
        except ValueError:
            msg = bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД:",
                                   reply_markup=create_back_only_keyboard())
            bot.register_next_step_handler(msg, process_recurring_end_date_step)

    def process_recurring_interval_step(message):
        chat_id = message.chat.id

        if message.text == '❌ Отмена':
            return_to_finance_menu(chat_id)
            return

        interval_map = {
            "Ежедневно": "1 day",
            "Еженедельно": "1 week",
            "Ежемесячно": "1 month",
            "Ежегодно": "1 year"
        }

        if message.text not in interval_map:
            msg = bot.send_message(chat_id, "Пожалуйста, выберите интервал из предложенных:",
                                   reply_markup=create_interval_options())
            bot.register_next_step_handler(msg, process_recurring_interval_step)
            return

        interval = interval_map[message.text]
        delta = user_data[chat_id]['end_date'] - user_data[chat_id]['start_date']
        min_days = {
            "1 day": 1,
            "1 week": 7,
            "1 month": 28,
            "1 year": 365
        }[interval]

        if delta.days < min_days:
            msg = bot.send_message(
                chat_id,
                f"Минимальный период для выбранного интервала - {min_days} дней. Введите новую дату окончания:",
                reply_markup=create_back_only_keyboard()
            )
            bot.register_next_step_handler(msg, process_recurring_end_date_step)
            return

        try:
            username = user_data[chat_id]['username']
            FinanceService.add_recurring_operation(
                amount=user_data[chat_id]['amount'],
                operation_type_id=user_data[chat_id]['operation_type_id'],
                category_id=user_data[chat_id].get('category_id'),
                client_id=FinanceService.get_client_id(username),
                family_id=FinanceService.get_family_id(username),
                date_start=user_data[chat_id]['start_date'],
                date_end=user_data[chat_id]['end_date'],
                payment_interval=interval
            )

            operation_type = user_data[chat_id]['operation_type'].lower()
            bot.send_message(chat_id, f"✅ Постоянный {operation_type} успешно добавлен!",
                             reply_markup=create_main_keyboard())
            cleanup_user_data(chat_id)

        except Exception as e:
            bot.send_message(chat_id, f"Ошибка: {str(e)}",
                             reply_markup=create_back_only_keyboard())
    '''
    (эта штука перекрывает кнопки 
        "Кредит",
        "Вклад",
        "Накопления",
        "Бюджет",
        "Назад" 
        Надо исправить как-то)

    @bot.message_handler(func=lambda m: True)
    def fallback_handler(message):
        bot.send_message(
            message.chat.id,
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=create_main_keyboard()
        )
    '''