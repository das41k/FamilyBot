# handlers/main_handlers.py
from ServiceAndrey import Part_Andrey
from keyboards import *

def register_main_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        username = message.from_user.username
        Part_Andrey.save_user_to_db(username)
        bot.send_message(
            message.chat.id,
            f"🏠 Привет, @{username}!",
            reply_markup=create_main_keyboard()
        )

    @bot.message_handler(func=lambda msg: msg.text == "👨👩👧👦 Семья")
    def handle_family_button(message):
        username = message.from_user.username
        bot.send_message(
            message.chat.id,
            "👨👩👧👦 Управление семьей",
            reply_markup=create_family_keyboard(username)
        )

    @bot.message_handler(func=lambda msg: msg.text == "💰 Учет финансов")
    def handle_finance_menu(message):
        bot.send_message(
            message.chat.id,
            "💼 Управление финансами",
            reply_markup=create_finance()
        )

    @bot.message_handler(func=lambda msg: msg.text == "📊 Статистика")
    def handle_statistics_menu(message):
        bot.send_message(
            message.chat.id,
            "📊Вывод статистики",
            reply_markup=create_statistics_types_keyboard()
        )