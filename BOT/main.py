# main.py
from BOT.bot_setup import create_bot
from Family.family_handlers import *
from Finance.finance_handlers import *
from Statistics.statistics_handlers import *
from main_handlers import register_main_handlers
from Calculation.calculation_handlers import *
from Info.info_handlers import *

def run_bot():
    bot = create_bot()
    # Регистрация всех обработчиков
    register_main_handlers(bot)
    register_family_handlers(bot)
    register_statistics_handlers(bot)
    register_finance_handlers(bot)
    register_calculation_handlers(bot)
    register_finance_handlers(bot)
    register_info_handlers(bot)
    print("Бот запущен...")
    bot.infinity_polling()


if __name__ == '__main__':
    run_bot()