from telebot import types
from BOT.keyboards import *

def register_info_handlers(bot):

    @bot.message_handler(func=lambda msg: msg.text == "↩️ Назад")
    def handle_back_to_main(message):
        print("[DEBUG] Пользователь нажал Назад в разделе информации")
        bot.send_message(
            message.chat.id,
            "🏠 Главное меню",
            reply_markup=create_main_keyboard()
        )

    @bot.message_handler(func=lambda msg: msg.text == "ℹ️ Информация")
    def handle_info_menu(message):
        print(f"[DEBUG] Пользователь {message.from_user.id} открыл меню информации")
        bot.send_message(
            message.chat.id,
            "ℹ️ <b>Раздел информации</b>\n\nВыберите, что вас интересует:",
            reply_markup=create_info_keyboard(),
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('info_'))
    def handle_info_callback(call):
        chat_id = call.message.chat.id
        try:
            if call.data == 'info_about_bot':
                text = (
                    "🤖 <b>О боте</b>\n\n"
                    "Этот бот поможет вам:\n"
                    "• Вести учёт доходов и расходов\n"
                    "• Получать детальную статистику\n"
                    "• Совместно контролировать семейный бюджет\n"
                    "• Следить за финансовыми целями и планами\n\n"
                    "Будьте в курсе своих финансов! 💰"
                )
            elif call.data == 'info_help':
                text = (
                    "📖 <b>Справка</b>\n\n"
                    "Быстрые команды:\n"
                    "• ➕ <b>Добавить расход</b> — сохранить покупку\n"
                    "• 📊 <b>Статистика</b> — посмотреть отчёты\n"
                    "• 🏡 <b>Семья</b> — управление семейным бюджетом\n"
                    "• ⚙️ <b>Настройки</b> — изменить параметры\n\n"
                    "Для получения помощи: напишите команду /help."
                )
            elif call.data == 'info_support':
                text = (
                    "🛠 <b>Поддержка и обратная связь</b>\n\n"
                    "Если у вас возникли вопросы, ошибки или предложения —\n"
                    "пишите напрямую разработчику: @YourUsername\n\n"
                    "Спасибо, что используете нашего бота! 🤝"
                )
            else:
                text = "❓ Неизвестный запрос."

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode='HTML'
            )

        except Exception as e:
            bot.send_message(chat_id, f"❌ Произошла ошибка при обработке запроса: {str(e)}")
            print(f"Error in handle_info_callback: {e}")
