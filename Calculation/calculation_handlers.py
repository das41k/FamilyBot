import telebot
from telebot import types
import datetime
import DBconnection
import ServiceAndrey
from ServiceAndrey import Part_Andrey
from Calculation.calculation_service import FinanceCalculator
from BOT.keyboards import *
from datetime import datetime, timedelta
user_data = {}

MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def get_month_year(month_num: int, start_date: datetime) -> str:
    """Возвращает 'Март 2024' с учетом смещения от start_date"""
    target_date = start_date
    for _ in range(month_num - 1):
        # Прибавляем примерно 1 месяц (упрощенный расчет)
        next_month = target_date.month % 12 + 1
        next_year = target_date.year + (1 if next_month == 1 else 0)
        target_date = target_date.replace(month=next_month, year=next_year)
    return f"{MONTHS_RU[target_date.month]} {target_date.year}"

def create_calculator_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Кредит",
        "Вклад",
        "Накопления",
        "↩️ Назад"  # Для возврата в главное меню
    ]
    keyboard.add(*buttons)
    return keyboard

def register_calculation_handlers(bot):

    # Открываем подменю калькулятора
    @bot.message_handler(func=lambda m: m.text == "Калькулятор финансов")
    def show_calculator_menu(message):
        bot.send_message(
            message.chat.id,
            "📊 Выберите тип расчета:",
            reply_markup=create_calculator_keyboard()
        )

    # Возврат в главное меню
    @bot.message_handler(func=lambda m: m.text == "↩️ Назад")
    def back_to_main_menu(message):
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=create_main_keyboard()
        )

    def create_retry_keyboard():
        """Клавиатура для повторного ввода с кнопкой отмены"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("🔙 Отменить ввод")
        return keyboard

    def handle_cancel(message) -> bool:
        """Универсальная проверка команды отмены"""
        if message.text.lower() in ("🔙 отменить ввод"):
            bot.send_message(
                message.chat.id,
                "🚫 Операция отменена",
                reply_markup=create_calculator_keyboard()
            )
            return True
        return False

    # ----------------- Кредитный калькулятор -----------------

    @bot.message_handler(func=lambda m: m.text == "Кредит")
    def ask_loan_type(message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Аннуитетный", "Дифференцированный", "↩️ Назад")
        bot.send_message(
            message.chat.id,
            "Выберите тип платежа:",
            reply_markup=keyboard
        )

    @bot.message_handler(func=lambda m: m.text in ["Аннуитетный", "Дифференцированный"])
    def ask_loan_amount(message):
        # Инициализируем или обновляем словарь, не перезаписывая полностью
        if message.chat.id not in user_data:
            user_data[message.chat.id] = {}

        user_data[message.chat.id]["loan_type"] = "annuity" if message.text == "Аннуитетный" else "diff"
        msg = bot.send_message(
            message.chat.id,
            "Введите сумму кредита (руб):",
            reply_markup=create_retry_keyboard()
        )
        bot.register_next_step_handler(msg, process_loan_amount)

    def process_loan_amount(message):
        """Обработка суммы кредита"""
        if handle_cancel(message):
            return

        try:
            amount = float(message.text)
            if not (0 < amount <= 200000000):
                raise ValueError

            user_data[message.chat.id]["amount"] = amount
            msg = bot.send_message(
                message.chat.id,
                "Введите годовую процентную ставку (например, 12.5):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_loan_rate)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная сумма! Введите положительное число до 200 000 000 (например: 500 000):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_loan_amount)

    def process_loan_rate(message):
        """Обработка процентной ставки"""
        if handle_cancel(message):
            return

        try:
            rate = float(message.text)
            if not (0.1 <= rate <= 100):  # Проверяем разумный диапазон ставок
                raise ValueError

            user_data[message.chat.id]["rate"] = rate
            msg = bot.send_message(
                message.chat.id,
                "Введите срок кредита в месяцах (от 1 до 360):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_loan_term)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная ставка! Введите число от 0.1 до 100 (например: 15.9):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_loan_rate)

    def process_loan_term(message):
        if handle_cancel(message):
            return

        try:
            term = int(message.text)
            if not (1 <= term <= 360):
                raise ValueError

            data = user_data[message.chat.id]
            # Явная проверка наличия loan_type
            if "loan_type" not in data:
                data["loan_type"] = "annuity"  # Значение по умолчанию
            loan_type = data.get("loan_type", "annuity")
            print(f"DEBUG: Input loan_type={data.get('loan_type')}")
            result = FinanceCalculator.calculate_loan(
                data["amount"],
                data["rate"],
                term,
                loan_type
            )

            # ДЛЯ ДЕБАГА - можно добавить временный вывод
            print(f"DEBUG: loan_type={loan_type}, result_type={result['payment_type']}")

            if result["payment_type"] == "annuity":
                # Вывод для аннуитета
                message_text = (
                    "🏦 <b>Аннуитетные платежи</b>\n\n"
                    f"• Сумма кредита: <b>{data['amount']:,.2f} руб</b>\n"
                    f"• Ставка: <b>{data['rate']}%</b>\n"
                    f"• Срок: <b>{term} мес</b>\n\n"
                    f"📅 Ежемесячный платёж: <b>{result['monthly_payment']:,.2f} руб</b>\n"
                    f"💸 Переплата: <b>{result['overpayment']:,.2f} руб</b>\n"
                    f"💰 Общая сумма: <b>{result['total_payment']:,.2f} руб</b>"
                )
                # Отправка аннуитетного платежа
                bot.send_message(
                    message.chat.id,
                    message_text,
                    parse_mode="HTML",
                    reply_markup=create_calculator_keyboard()
                )
            else:
                # Вывод для дифференцированных платежей
                header = (
                    "🏦 <b>Дифференцированные платежи</b>\n\n"
                    f"• Сумма кредита: <b>{data['amount']:,.2f} руб</b>\n"
                    f"• Ставка: <b>{data['rate']}%</b>\n"
                    f"• Срок: <b>{term} мес</b>\n\n"
                    f"📈 Первый платёж: <b>{result['first_payment']:,.2f} руб</b>\n"
                    f"📉 Последний платёж: <b>{result['last_payment']:,.2f} руб</b>\n"
                    f"💸 Переплата: <b>{result['overpayment']:,.2f} руб</b>\n\n"
                    "<b>График платежей:</b>\n"
                )

                max_rows_per_message = 12  # Месяцев на сообщение
                schedule = result["schedule"]

                for i in range(0, len(schedule), max_rows_per_message):
                    chunk = schedule[i:i + max_rows_per_message]

                    table = "<pre>\n"
                    table += "┌────────────────┬────────────────┬────────────────┐\n"
                    table += "│     Месяц      │     Платёж     │    Остаток     │\n"
                    table += "├────────────────┼────────────────┼────────────────┤\n"

                    current_date = datetime.now()
                    for p in chunk:
                        month = get_month_year(p['month'], current_date).rjust(14)
                        payment = f"{p['payment']:,.2f}".replace(",", " ").rjust(14)
                        remaining = f"{p['remaining']:,.2f}".replace(",", " ").rjust(14)
                        table += f"│ {month} │ {payment} │ {remaining} │\n"

                    table += "└────────────────┴────────────────┴────────────────┘\n"
                    table += "</pre>"

                    # Собираем сообщение
                    message_text = header if i == 0 else ""  # Заголовок только в первом сообщении
                    message_text += table

                    # Проверка длины сообщения (макс. 4096 символов)
                    if len(message_text) > 4096:
                        raise ValueError("Сообщение слишком длинное")

                    # Отправка части таблицы
                    bot.send_message(
                        message.chat.id,
                        message_text,
                        parse_mode="HTML",
                        reply_markup=create_calculator_keyboard() if (i + max_rows_per_message >= len(schedule)) else None
                    )

            bot.clear_step_handler(message)

        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректный срок! Введите целое число от 1 до 360 (например: 36):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_loan_term)

    # ----------------- Калькулятор вкладов -----------------

    @bot.message_handler(func=lambda m: m.text == "Вклад")
    def ask_deposit_type(message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("С капитализацией", "Без капитализации", "↩️ Назад")
        bot.send_message(
            message.chat.id,
            "📈 Выберите тип вклада:",
            reply_markup=keyboard
        )

    # Шаг 1: Выбор типа вклада и ввод суммы
    @bot.message_handler(func=lambda m: m.text in ["С капитализацией", "Без капитализации"])
    def ask_deposit_amount(message):
        # Сохраняем тип вклада
        user_data[message.chat.id] = {
            "deposit_type": "capitalization" if message.text == "С капитализацией" else "simple"
        }

        msg = bot.send_message(
            message.chat.id,
            "Введите сумму вклада (руб):",
            reply_markup=create_retry_keyboard()
        )
        bot.register_next_step_handler(msg, process_deposit_amount)

    # Шаг 2: Обработка суммы и ввод ставки
    def process_deposit_amount(message):
        if handle_cancel(message):
            return

        try:
            amount = float(message.text)
            if not (0 < amount <= 1400000):
                raise ValueError

            user_data[message.chat.id]["amount"] = amount

            msg = bot.send_message(
                message.chat.id,
                "Введите годовую процентную ставку (например: 18.5):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_deposit_rate)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная сумма! Введите положительное число до 1 400 000 (например: 500 000):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_deposit_amount)

    # Шаг 3: Обработка ставки и ввод срока
    def process_deposit_rate(message):
        if handle_cancel(message):
            return

        try:
            rate = float(message.text)
            if not (0.1 <= rate <= 100):
                raise ValueError

            user_data[message.chat.id]["rate"] = rate

            msg = bot.send_message(
                message.chat.id,
                "Введите срок в месяцах (от 1 до 36):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_deposit_term)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная ставка! Введите число от 0.1 до 100 (например: 15.9):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_deposit_rate)

    # Шаг 4: Расчет и вывод результата
    def process_deposit_term(message):
        if handle_cancel(message):
            return

        try:
            term = int(message.text)
            if not (1 <= term <= 36):
                raise ValueError
            data = user_data[message.chat.id]

            result = FinanceCalculator.calculate_deposit(
                data["amount"],
                data["rate"],
                term,
                data["deposit_type"]
            )
            schedule = FinanceCalculator.generate_deposit_schedule(
                data["amount"],
                data["rate"],
                term,
                data["deposit_type"]
            )

            #1 Форматируем результат
            text = (
                "🏦 Результаты расчета вклада:\n\n"
                f"▫️ Тип вклада: <b>{'с капитализацией' if data['deposit_type'] == 'capitalization' else 'без капитализации'}</b>\n"
                f"• Сумма: <b>{data['amount']:,.2f} руб</b>\n"
                f"• Ставка: <b>{data['rate']}%</b>\n"
                f"• Срок: <b>{term} мес</b>\n"
                f"• Итоговая сумма: <b>{result['total']:,.2f} руб</b>\n"
                f"• Начисленные проценты: <b>{result['interest']:,.2f} руб</b>\n\n"
                "<b>Подробный график:</b>"
            )

            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML"
            )

            # 2. Затем отправляем таблицу с графиком
            current_date = datetime.now()
            table = "<pre>"
            table += "┌────────────────┬────────────────┬────────────────┐\n"
            table += "│     Месяц      │   Начислено %  │      Итого     │\n"
            table += "├────────────────┼────────────────┼────────────────┤\n"

            for p in schedule:
                month_str = get_month_year(p["month"], current_date).rjust(14)
                interest_str = f"{p['interest']:,.2f}".replace(",", " ").rjust(14)
                amount_str = f"{p['end_amount']:,.2f}".replace(",", " ").rjust(14)

                table += f"│ {month_str} │ {interest_str} │ {amount_str} │\n"

            table += "└────────────────┴────────────────┴────────────────┘\n"
            table += "</pre>"

            # Проверка длины сообщения (макс. 4096 символов)
            if len(table) > 4096:
                raise ValueError("Сообщение слишком длинное")

            bot.send_message(
                message.chat.id,
                table,
                parse_mode="HTML",
                reply_markup=create_calculator_keyboard()  # Клавиатура только под таблицей
            )

        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректный срок! Введите целое число от 1 до 36 (например: 12):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_deposit_term)

    # ----------------- Накопительный калькулятор -----------------

    @bot.message_handler(func=lambda m: m.text == "Накопления")
    def start_savings(message):
        msg = bot.send_message(
            message.chat.id,
            "💵 Введите начальную сумму:",
            reply_markup = create_retry_keyboard()
        )
        bot.register_next_step_handler(msg, process_initial_sum)

    def process_initial_sum(message):
        if handle_cancel(message):
            return

        try:
            amount = float(message.text)
            if not (0 < amount <= 100000000):
                raise ValueError
            user_data[message.chat.id] = {
                "initial": amount,
                "step": "await_monthly_add"
            }
            msg = bot.send_message(
                message.chat.id,
                "📥 Введите ежемесячное пополнение:",
                reply_markup = create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_monthly_add)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная сумма! Введите положительное число до 100 000 000 (например: 50 000):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_initial_sum)

    def process_monthly_add(message):
        if handle_cancel(message):
            return

        try:
            monthly_add = float(message.text)
            if monthly_add < 0:
                raise ValueError
            user_data[message.chat.id].update({
                "monthly_add": monthly_add,
                "step": "await_months"
            })
            msg = bot.send_message(
                message.chat.id,
                "⏳ Введите срок в месяцах от 1 до 36:",
                reply_markup = create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_months)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная сумма пополнения! Введите неотрицательное число (например: 10 000):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_monthly_add)

    def process_months(message):
        if handle_cancel(message):
            return

        try:
            months = int(message.text)
            if not 1 <= months <= 36:
                raise ValueError

            user_data[message.chat.id].update({
                "months": months,
                "step": "await_rate"
            })
            msg = bot.send_message(
                message.chat.id,
                "📈 Введите годовую процентную ставку (%):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_rate)
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректный срок! Введите целое число от 1 до 36 (например: 12):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_months)

    def process_rate(message):
        if handle_cancel(message):
            return

        try:
            rate = float(message.text)
            if not (0.1 <= rate <= 100):
                raise ValueError
            data = user_data[message.chat.id]
            current_date = datetime.now()

            # Выполняем расчёт
            result = FinanceCalculator.calculate_savings_comparison(
                initial=data["initial"],
                monthly_add=data["monthly_add"],
                months=data["months"],
                annual_rate=rate
            )

            # Формируем ответ
            response = (
                f"🏦 Результаты расчета накопительного счета :\n\n"
                f"• Начальная сумма: <b>{data['initial']:,.2f} руб</b>\n"
                f"• Ежемесячное пополнение: <b>{data['monthly_add']:,.2f} руб</b>\n"
                f"• Срок: <b>{data['months']} мес</b>\n"
                f"• Ставка: <b>{rate}%</b>\n\n"
                f"<b>С капитализацией:</b>\n"
                f"💵 Итоговая сумма: <b>{result['with_cap']['total']:,.2f} руб</b>\n"
                f"💸 Начисленные проценты: <b>{result['with_cap']['total_interest']:,.2f} руб</b>\n\n"
                f"<b>Без капитализации:</b>\n"
                f"💵 Итоговая сумма: <b>{result['without_cap']['total']:,.2f} руб</b>\n"
                f"💸 Начисленные проценты: <b>{result['without_cap']['total_interest']:,.2f} руб</b>\n\n"
            )

            # Генерируем таблицы
            def generate_table(schedule, title):
                table = f"<b>{title}</b>\n<pre>"
                table += "┌────────────────┬────────────────┬────────────────┬────────────────┐\n"
                table += "│     Месяц      │   Пополнение   │   Начислено    │ Общий остаток  │\n"
                table += "├────────────────┼────────────────┼────────────────┼────────────────┤\n"

                for p in schedule:
                    date_str = get_month_year(p['month'], current_date).rjust(14)
                    added_str = f"{p['added']:,.2f}".rjust(14)
                    interest_str = f"{p['interest']:,.2f}".rjust(14)
                    total_str = f"{p['total']:,.2f}".rjust(14)
                    table += (
                        f"│ {date_str} │ {added_str} │ {interest_str} │ {total_str} │\n"
                    )

                table += "└────────────────┴────────────────┴────────────────┴────────────────┘</pre>"
                return table

            bot.send_message(
                message.chat.id,
                response,
                parse_mode="HTML"
            )

            # Отправляем таблицу с капитализацией
            bot.send_message(
                message.chat.id,
                generate_table(result['with_cap']['schedule'], 'С капитализацией:'),
                parse_mode="HTML"
            )

            # Отправляем таблицу без капитализации
            bot.send_message(
                message.chat.id,
                generate_table(result['without_cap']['schedule'], 'Без капитализации:'),
                parse_mode="HTML",
                reply_markup=create_calculator_keyboard()  # Клавиатура только под последним сообщением
            )

        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Некорректная ставка! Введите число от 0.1 до 100 (например: 15.9):",
                reply_markup=create_retry_keyboard()
            )
            bot.register_next_step_handler(msg, process_rate)

    @bot.message_handler(func=lambda m: True)
    def fallback_handler(message):
        bot.send_message(
            message.chat.id,
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=create_main_keyboard()
        )