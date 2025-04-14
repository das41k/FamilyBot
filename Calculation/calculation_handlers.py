import telebot
from telebot import types
import datetime
import DBconnection
import ServiceAndrey
from ServiceAndrey import Part_Andrey
from Calculation.calculation_service import FinanceCalculator
from BOT.keyboards import *
user_data = {}

def create_calculator_keyboard():
    '''
    "Вклад",
    "Накопления",
    "Бюджет",
    '''
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Кредит",
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
            if amount <= 0:
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
                "⚠️ Некорректная сумма! Введите положительное число (например: 500000):",
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

                    # Формируем часть таблицы
                    table = "<pre>"  # Начало тега <pre>
                    table += "┌───────┬─────────────┬───────────┐\n"
                    table += "│  Мес. │   Платёж    │  Остаток  │\n"
                    table += "├───────┼─────────────┼───────────┤\n"

                    for p in chunk:
                        # Форматируем числа с пробелами вместо запятых
                        payment_str = f"{p['payment']:,.2f}".replace(",", " ")
                        remaining_str = f"{p['remaining']:,.2f}".replace(",", " ")

                        table += (
                            f"│ {p['month']:^5} │ "
                            f"{payment_str:>11} │ "
                            f"{remaining_str:>9} │\n"
                        )

                    table += "└───────┴─────────────┴───────────┘\n"
                    table += "</pre>"  # Закрываем тег

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
    @bot.message_handler(func=lambda m: True)
    def fallback_handler(message):
        bot.send_message(
            message.chat.id,
            "Пожалуйста, используйте кнопки меню.",
            reply_markup=create_main_keyboard()
        )