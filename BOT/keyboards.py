# keyboards.py
from telebot import types
from Family.family_service import family_service
from Finance.finance_service import FinanceService
def create_main_keyboard():
    """Главное меню"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("👨👩👧👦 Семья", "💰 Учет финансов")
    keyboard.row("📊 Статистика")
    return keyboard

def create_family_keyboard(username):
    """Меню функций семьи"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if family_service.get_family_id(username):
        keyboard.row("👪 Моя семья", "🚪 Выйти")
    else:
        keyboard.row("➕ Создать", "🔗 Присоединиться")

    keyboard.row("↩️ Назад")
    return keyboard

def create_finance():
    """Меню финансового учета"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "💸 Добавить расход",
        "💰 Добавить доход",
        "🔄 Постоянный расход",
        "🔄 Постоянный доход"
    ]
    keyboard.add(*buttons)
    keyboard.row("↩️ Назад")
    return keyboard

def create_categories_keyboard(operation_type="Расход"):
    """Клавиатура с категориями"""
    categories = FinanceService.get_categories_from_db()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    keyboard.add(*categories.keys())
    keyboard.row("❌ Отмена")
    return keyboard

def create_statistics_types_keyboard():
    """Клавиатура выбора типа статистики (inline)"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton("📊 Общая статистика семьи", callback_data='stat_family_overview'),
        types.InlineKeyboardButton("📈 Динамика доходов/расходов", callback_data='stat_dynamics'),
        types.InlineKeyboardButton("🔄 Расходы по категориям", callback_data='stat_categories'),
        types.InlineKeyboardButton("👤 Личная статистика", callback_data='stat_personal')
    ]
    keyboard.add(*buttons)
    return keyboard

def create_statistics_period_keyboard(stat_type):
    """Клавиатура выбора периода для статистики (inline)"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("Неделя", callback_data=f'stat_period|{stat_type}|week'),
        types.InlineKeyboardButton("Месяц", callback_data=f'stat_period|{stat_type}|month'),
        types.InlineKeyboardButton("Год", callback_data=f'stat_period|{stat_type}|year'),
        types.InlineKeyboardButton("Свой период", callback_data=f'stat_period|{stat_type}|custom')
    ]
    keyboard.add(*buttons)
    return keyboard

def create_confirm_keyboard():
    """Клавиатура подтверждения"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("✅ Да", "❌ Нет")
    return keyboard
