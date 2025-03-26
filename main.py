import telebot
from telebot import types
import DBconnection

bot = telebot.TeleBot('7795186444:AAE-M2N6ywh9PmjUwAzz-A6h39Rc9fvDzj0')
# Создаем клавиатуру
def create_reply_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Добавить расходы",
        "Показать статистику",
        "Установить лимиты",
        "Настроить уведомления",
        "Установить цели",
        "Сравнить с другими",
        "Достижения",
        "Черный список",
        "Постоянные доходы/расходы"
    ]
    keyboard.add(*buttons)
    return keyboard
# Edited here `15151216166161611661616161
# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = create_reply_keyboard()
    bot.send_message(message.chat.id, "Привет! Чем могу помочь?", reply_markup=keyboard)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Добавить расходы":
        bot.send_message(message.chat.id, "Введите сумму и категорию расхода.")
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

# Запуск бота
bot.infinity_polling()