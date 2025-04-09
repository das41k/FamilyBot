import datetime
import os

from BOT.keyboards import *
from Statistics.statistics_service import *

user_data = {}


def register_statistics_handlers(bot):
    @bot.message_handler(func=lambda msg: msg.text == "↩️ Назад")
    def handle_back(message):
        print("[DEBUG] Обработка кнопки Назад в статистике")  # Отладочное сообщение
        bot.send_message(
            message.chat.id,
            "🏠 Главное меню",
            reply_markup=create_main_keyboard()
        )

    @bot.message_handler(func=lambda msg: msg.text == "📊 Статистика")
    def handle_statistics_menu(message):
        print(f"[DEBUG] Пользователь {message.from_user.id} открыл меню статистики")  # Отладочное сообщение
        bot.send_message(message.chat.id, "📊 <b>Выберите тип статистики:</b>",
                         reply_markup=create_statistics_types_keyboard(), parse_mode='HTML')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('stat_'))
    def handle_statistics_callback(call):
        chat_id = call.message.chat.id
        username = call.from_user.username

        try:
            client_info = StatService.get_client_info_by_tg_nick(username)
            if not client_info:
                bot.send_message(chat_id, "❌ Пользователь не найден в системе")
                return

            if call.data == 'stat_family_overview':
                if not client_info['family_id']:
                    bot.send_message(chat_id, "❌ Вы не состоите в семье")
                    return

                bot.send_message(chat_id, "⏳ Готовим статистику семьи...")
                family_stats_file = StatService.get_stat_family_operation(client_info['family_id'])
                with open(family_stats_file, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption="📊 <b>Общая статистика семьи</b>", parse_mode='HTML')
                os.remove(family_stats_file)

                users_stats_files = StatService.get_stat_familyUsers_operation(client_info['family_id'])
                if isinstance(users_stats_files, list):
                    for file in users_stats_files:
                        with open(file, 'rb') as photo:
                            bot.send_photo(chat_id, photo)
                        os.remove(file)
                elif users_stats_files:
                    with open(users_stats_files, 'rb') as photo:
                        bot.send_photo(chat_id, photo, caption="👨‍👩‍👧‍👦 <b>Статистика участников семьи</b>",
                                       parse_mode='HTML')
                    os.remove(users_stats_files)

            elif call.data in ['stat_family_dynamics', 'stat_user_dynamics',
                               'stat_family_categories', 'stat_user_categories']:
                show_date_range_keyboard(chat_id, call.data, client_info)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка при получении статистики: {str(e)}")
            print(f"Error in handle_statistics_callback: {e}")

    def show_date_range_keyboard(chat_id, stat_type, client_info):
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Неделя", callback_data=f'date_range|{stat_type}|week'),
            types.InlineKeyboardButton("Месяц", callback_data=f'date_range|{stat_type}|month'),
            types.InlineKeyboardButton("Год", callback_data=f'date_range|{stat_type}|year'),
            types.InlineKeyboardButton("Свой вариант", callback_data=f'date_range|{stat_type}|custom'),
        ]
        keyboard.add(*buttons)
        bot.send_message(chat_id, "📅 Выберите период:", reply_markup=keyboard)

        # Сохраняем тип статистики и информацию о клиенте
        user_data[chat_id] = {
            'stat_type': stat_type,
            'client_info': client_info
        }

    @bot.callback_query_handler(func=lambda call: call.data.startswith('date_range'))
    def handle_date_range_selection(call):
        chat_id = call.message.chat.id
        _, stat_type, range_type = call.data.split('|')

        try:
            user_info = user_data.get(chat_id, {})
            client_info = user_info.get('client_info')

            if range_type == 'custom':
                msg = bot.send_message(chat_id, "📅 Введите период в формате (ГГГГ-ММ-ДД ГГГГ-ММ-ДД):\n"
                                                "Например: 2023-01-01 2023-12-31")
                bot.register_next_step_handler(msg, process_statistics_period)
            else:
                end_date = datetime.date.today()
                if range_type == 'week':
                    start_date = end_date - datetime.timedelta(days=7)
                elif range_type == 'month':
                    start_date = end_date - datetime.timedelta(days=30)
                elif range_type == 'year':
                    start_date = end_date - datetime.timedelta(days=365)

                process_statistics_period_with_dates(chat_id, stat_type, start_date, end_date, client_info)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка при обработке запроса: {str(e)}")

    def process_statistics_period(message):
        chat_id = message.chat.id
        user_info = user_data.get(chat_id, {})

        try:
            dates = message.text.split()
            if len(dates) != 2:
                raise ValueError("Неверный формат периода. Используйте ГГГГ-ММ-ДД ГГГГ-ММ-ДД")

            start_date, end_date = dates
            datetime.datetime.strptime(start_date, "%Y-%m-%d")
            datetime.datetime.strptime(end_date, "%Y-%m-%d")

            stat_type = user_info.get('stat_type')
            client_info = user_info.get('client_info')

            process_statistics_period_with_dates(chat_id, stat_type, start_date, end_date, client_info)

        except ValueError as e:
            bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Произошла ошибка при обработке запроса - нет данных для отображения")
            print(f"Error in process_statistics_period: {e}")

    def process_statistics_period_with_dates(chat_id, stat_type, start_date, end_date, client_info):
        try:
            if stat_type == 'stat_family_dynamics':
                if not client_info['family_id']:
                    bot.send_message(chat_id, "❌ Вы не состоите в семье")
                    return

                bot.send_message(chat_id, "⏳ Готовим график динамики семьи...")
                stats_file = StatService.get_income_expense_time_series(
                    client_info['family_id'], start_date, end_date
                )
                caption = f"📈 <b>Динамика доходов и расходов семьи</b>\n" \
                          f"Период: {start_date} - {end_date}"

            elif stat_type == 'stat_user_dynamics':
                bot.send_message(chat_id, "⏳ Готовим график личной динамики...")
                stats_file = StatService.get_client_income_expense_time_series(
                    client_info['client_id'], start_date, end_date
                )
                caption = f"📉 <b>Динамика личных доходов и расходов</b>\n" \
                          f"Период: {start_date} - {end_date}"

            elif stat_type == 'stat_family_categories':
                if not client_info['family_id']:
                    bot.send_message(chat_id, "❌ Вы не состоите в семье")
                    return

                bot.send_message(chat_id, "⏳ Готовим диаграмму расходов семьи...")
                stats_file = StatService.get_stat_family_category_with_chart_by_date(
                    client_info['family_id'], start_date, end_date
                )
                caption = f"🔄 <b>Распределение расходов семьи по категориям</b>\n" \
                          f"Период: {start_date} - {end_date}"

            elif stat_type == 'stat_user_categories':
                bot.send_message(chat_id, "⏳ Готовим диаграмму личных расходов...")
                stats_file = StatService.get_stat_client_category_with_chart_by_date(
                    client_info['client_id'], start_date, end_date
                )
                caption = f"🔄 <b>Распределение личных расходов по категориям</b>\n" \
                          f"Период: {start_date} - {end_date}"

            else:
                raise ValueError("Неизвестный тип статистики")

            with open(stats_file, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=caption, parse_mode='HTML')
            os.remove(stats_file)

        except ValueError as e:
            bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Произошла ошибка при обработке запроса - нет данных для отображения")
            print(f"Error in process_statistics_period_with_dates: {e}")
