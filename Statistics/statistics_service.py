import matplotlib
matplotlib.use('agg')  # Используем backend, который не требует GUI

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rc
from matplotlib.patheffects import withStroke
import datetime
from DBconnection import connection
import matplotlib.dates as mdates

rc('font', family='DejaVu Sans')

class StatService:
    # Соединение с базой данных как атрибут класса
    _connection = connection

    @staticmethod
    def get_stat_client_category_by_date(client_id: int, start_date: str, end_date: str) -> dict:
        """Получить статистику РАСХОДОВ клиента по категориям за период"""
        try:
            with StatService._connection.cursor() as cursor:
                # Получаем общую сумму РАСХОДОВ за период
                total_query = """
                           SELECT COALESCE(SUM(amount), 0)
                           FROM Operations
                           WHERE client_id = %s
                           AND operation_type_id = 2  -- Только расходы
                           AND operation_date BETWEEN %s AND %s;
                       """
                cursor.execute(total_query, (client_id, start_date, end_date))
                total_amount = cursor.fetchone()[0] or 1

                # Получаем данные по категориям (только РАСХОДЫ)
                stat_query = """
                           SELECT
                               c.category_id,
                               c.category_name,
                               COALESCE(SUM(o.amount), 0) as amount,
                               (COALESCE(SUM(o.amount), 0) * 100.0 / %s) as percentage
                           FROM Categories c
                           JOIN Operations o ON c.category_id = o.category_id
                               AND o.client_id = %s
                               AND o.operation_type_id = 2  -- Только расходы
                               AND o.operation_date BETWEEN %s AND %s
                           GROUP BY c.category_id, c.category_name
                           HAVING COALESCE(SUM(o.amount), 0) > 0
                           ORDER BY amount DESC;
                       """
                cursor.execute(stat_query, (total_amount, client_id, start_date, end_date))
                result = cursor.fetchall()
                return {
                    'total_amount': total_amount,
                    'start_date': start_date,
                    'end_date': end_date,
                    'categories': [
                        {
                            'category_id': row[0],
                            'category_name': row[1],
                            'amount': float(row[2]),
                            'percentage': float(row[3])
                        } for row in result
                    ]
                }
        except Exception as e:
            print(f"Ошибка при получении статистики клиента: {e}")
        return {'total_amount': 0, 'categories': []}

    @staticmethod
    def _create_pie_chart(data: dict, title_prefix: str, period_info: str = None):
        """Версия с темной темой и уникальными цветами категорий"""
        if not data.get('categories'):
            print("Нет данных для отображения")
            return None

        # Настройки темной темы
        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 11
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'

        # Подготовка данных
        categories = [cat['category_name'] for cat in data['categories']]
        amounts = [cat['amount'] for cat in data['categories']]
        percentages = [cat['percentage'] for cat in data['categories']]
        total = data['total_amount']

        # Создание фигуры с темным фоном
        fig, ax = plt.subplots(figsize=(13, 9))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#1E1E1E')

        # Уникальные насыщенные цвета для категорий
        category_colors = {
            'Еда': '#FF6B6B',
            'Жилье': '#4ECDC4',
            'Транспорт': '#45B7D1',
            'Спорт': '#FFA07A',
            'Одежда': '#A28DFF',
            'Подарки': '#FFD166',
            'Развлечения': '#6A0572',
            'Здоровье': '#06D6A0',
            'Образование': '#118AB2',
            'Другое': '#EF476F'
        }

        colors = [category_colors.get(cat, '#43AA8B') for cat in categories]

        # Построение диаграммы
        wedges, texts, autotexts = ax.pie(
            amounts,
            autopct=lambda p: f'{p:.1f}%',
            startangle=90,
            wedgeprops={'linewidth': 1, 'edgecolor': '#333333', 'alpha': 0.85},
            textprops={
                'fontsize': 11,
                'fontweight': 'bold',
                'color': 'white',
                'bbox': dict(boxstyle='round,pad=0.2', fc='#333333', alpha=0.7)
            },
            pctdistance=0.75,
            colors=colors,
            explode=[0.03] * len(categories),
            rotatelabels=True
        )

        # Настройка текста процентов
        for text in autotexts:
            text.set_rotation_mode('anchor')
            if float(text.get_text().replace('%', '')) < 5:
                text.set_fontsize(9)
                text.set_position((text.get_position()[0] * 1.2, text.get_position()[1] * 1.2))

        # Заголовок
        title = f'{title_prefix}\nОбщая сумма: {total:.2f}Р'
        if period_info:
            title = f'{title_prefix}\nЗа период {period_info}\nОбщая сумма: {total:.2f}Р'

        ax.set_title(title, pad=25, fontsize=14, fontweight='bold', color='white')

        # Легенда с белым текстом
        legend_labels = [f"{cat}: {amt:.2f}Р ({perc:.1f}%)"
                         for cat, amt, perc in zip(categories, amounts, percentages)]

        legend = ax.legend(
            wedges,
            legend_labels,
            title="Категории расходов",
            loc="center left",
            bbox_to_anchor=(1.05, 0.5),
            fontsize=10,
            frameon=True,
            framealpha=0.7,
            edgecolor='#444444',
            facecolor='#222222',
            labelcolor='white'
        )
        legend.get_title().set_color('white')
        legend.get_title().set_fontsize(12)

        # Центральный круг
        centre_circle = plt.Circle((0, 0), 0.4, fc='#222222', edgecolor='#444444')
        ax.add_artist(centre_circle)

        # Настройка расположения
        plt.tight_layout(rect=[0, 0, 0.85, 1])
        plt.subplots_adjust(right=0.8)

        # Сохраняем график в файл
        temp_file_categories = "family_categories_stats.png"
        fig.savefig(temp_file_categories, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Закрываем фигуру после сохранения

        return temp_file_categories

    @staticmethod
    def get_stat_family_category_by_date(family_id: int, start_date: str, end_date: str) -> dict:
        """Получить статистику РАСХОДОВ семьи по категориям за период"""
        try:
            with StatService._connection.cursor() as cursor:
                # Получаем общую сумму РАСХОДОВ за период
                total_query = """
                            SELECT COALESCE(SUM(amount), 0)
                            FROM Operations
                            WHERE family_id = %s
                            AND operation_type_id = 2  -- Только расходы
                            AND operation_date BETWEEN %s AND %s;
                        """
                cursor.execute(total_query, (family_id, start_date, end_date))
                total_amount = cursor.fetchone()[0] or 1

                # Получаем данные по категориям (только РАСХОДЫ)
                stat_query = """
                            SELECT
                                c.category_id,
                                c.category_name,
                                COALESCE(SUM(o.amount), 0) as amount,
                                (COALESCE(SUM(o.amount), 0) * 100.0 / %s) as percentage
                            FROM Categories c
                            JOIN Operations o ON c.category_id = o.category_id
                                AND o.family_id = %s
                                AND o.operation_type_id = 2  -- Только расходы
                                AND o.operation_date BETWEEN %s AND %s
                            GROUP BY c.category_id, c.category_name
                            HAVING COALESCE(SUM(o.amount), 0) > 0
                            ORDER BY amount DESC;
                        """
                cursor.execute(stat_query, (total_amount, family_id, start_date, end_date))
                result = cursor.fetchall()

                return {
                    'total_amount': total_amount,
                    'start_date': start_date,
                    'end_date': end_date,
                    'categories': [
                        {
                            'category_id': row[0],
                            'category_name': row[1],
                            'amount': float(row[2]),
                            'percentage': float(row[3])
                        } for row in result
                    ]
                }
        except Exception as e:
            print(f"Ошибка при получении статистики семьи: {e}")
            return {'total_amount': 0, 'categories': []}

    @staticmethod
    def get_client_income_expense_by_date(client_id: int, start_date: str, end_date: str) -> dict:
        """Получение данных о доходах и расходах по дням для клиента"""
        try:
            with StatService._connection.cursor() as cursor:
                # Запрос для получения доходов и расходов по дням
                query = """
                       SELECT
                           operation_date as date,
                           SUM(CASE WHEN operation_type_id = 1 THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN operation_type_id = 2 THEN amount ELSE 0 END) as expense
                       FROM operations
                       WHERE client_id = %s
                       AND operation_date BETWEEN %s AND %s
                       GROUP BY operation_date
                       ORDER BY operation_date;
                   """
                cursor.execute(query, (client_id, start_date, end_date))
                result = cursor.fetchall()

                # Преобразуем результат в словарь с списками
                dates = []
                income = []
                expenses = []

                for row in result:
                    dates.append(row[0].strftime('%Y-%m-%d'))
                    income.append(float(row[1]))
                    expenses.append(float(row[2]))

                return {
                    'dates': dates,
                    'income': income,
                    'expenses': expenses
                }
        except Exception as e:
            print(f"Ошибка при получении данных по дням: {e}")
            return {'dates': [], 'income': [], 'expenses': []}

    @staticmethod
    def get_total_expenses_for_user(client_id):
        """Получение общей суммы расходов определённого пользователя."""
        with StatService._connection.cursor() as cursor:
            query = """
                SELECT SUM(amount)
                FROM operations
                WHERE client_id = %s AND operation_type_id = 2;
                """
            cursor.execute(query, (client_id,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0

    @staticmethod
    def get_income_expense_by_date(family_id: int, start_date: str, end_date: str) -> dict:
        """Получение данных о доходах и расходах по дням для семьи"""
        try:
            with StatService._connection.cursor() as cursor:
                # Запрос для получения доходов и расходов по дням
                query = """
                        SELECT
                            operation_date as date,
                            SUM(CASE WHEN operation_type_id = 1 THEN amount ELSE 0 END) as income,
                            SUM(CASE WHEN operation_type_id = 2 THEN amount ELSE 0 END) as expense
                        FROM operations
                        WHERE family_id = %s
                        AND operation_date BETWEEN %s AND %s
                        GROUP BY operation_date
                        ORDER BY operation_date;
                    """
                cursor.execute(query, (family_id, start_date, end_date))
                result = cursor.fetchall()

                # Преобразуем результат в словарь с списками
                dates = []
                income = []
                expenses = []

                for row in result:
                    dates.append(row[0].strftime('%Y-%m-%d'))
                    income.append(float(row[1]))
                    expenses.append(float(row[2]))

                return {
                    'dates': dates,
                    'income': income,
                    'expenses': expenses
                }
        except Exception as e:
            print(f"Ошибка при получении данных по дням: {e}")
            return {'dates': [], 'income': [], 'expenses': []}

    @staticmethod
    def _create_income_expense_time_series(data: dict, title_prefix: str, period_info: str = None):
        """Создание графика доходов и расходов по времени"""
        if not data.get('dates') or (not data.get('income') and not data.get('expenses')):
            print("Нет данных для отображения")
            return None

        # Настройки темной темы
        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 11
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(13, 7))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#1E1E1E')

        # Подготовка данных
        dates = data['dates']
        income = data.get('income', [0] * len(dates))
        expenses = data.get('expenses', [0] * len(dates))

        # Преобразуем даты в datetime для правильного отображения
        date_objects = [datetime.datetime.strptime(date, '%Y-%m-%d') for date in dates]

        # Определяем минимальную и максимальную даты из данных
        min_date = min(date_objects)
        max_date = max(date_objects)

        # Добавляем небольшой отступ справа (например, 5% от диапазона дат)
        date_range = max_date - min_date
        padding = date_range * 0.05
        xlim_max = max_date + padding

        # Построение графиков
        if any(income):
            ax.plot(date_objects, income,
                    label='Доходы',
                    color='#06D6A0',
                    linewidth=2.5,
                    marker='o',
                    markersize=6)

        if any(expenses):
            ax.plot(date_objects, expenses,
                    label='Расходы',
                    color='#EF476F',
                    linewidth=2.5,
                    marker='o',
                    markersize=6)

        # Устанавливаем пределы оси X
        ax.set_xlim(min_date - padding, xlim_max)

        # Настройка осей и сетки
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Сумма (руб)', fontsize=12)

        # Форматирование дат на оси X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        fig.autofmt_xdate()  # Наклон подписей дат

        # Заголовок
        title = f'{title_prefix}\nДинамика доходов и расходов'
        if period_info:
            title = f'{title_prefix}\nДинамика доходов и расходов за период {period_info}'

        ax.set_title(title, pad=20, fontsize=14, fontweight='bold')

        # Легенда
        ax.legend(
            loc='upper left',
            fontsize=10,
            frameon=True,
            framealpha=0.7,
            edgecolor='#444444',
            facecolor='#222222',
            labelcolor='white'
        )

        # Сохраняем график в файл
        temp_file = "income_expense_timeseries.png"
        fig.savefig(temp_file, dpi=300, bbox_inches='tight')
        plt.close(fig)

        return temp_file

    @staticmethod
    def get_client_for_family(family_id):
        with StatService._connection.cursor() as cursor:
            query = """
                       SELECT * from CLIENTS
                       WHERE family_id = %s;
                       """
            cursor.execute(query, (family_id,))
            result = cursor.fetchall()
            return result

    @staticmethod
    def get_total_expenses_for_family(family_id):
        """Получение общей суммы расходов для семьи."""
        with StatService._connection.cursor() as cursor:
            query = """
                  SELECT SUM(amount)
                  FROM operations
                  WHERE family_id = %s AND operation_type_id = 2;
                  """
            cursor.execute(query, (family_id,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0

    @staticmethod
    def get_total_income_for_family(family_id):
        """Получение общей суммы доходов для семьи."""
        with StatService._connection.cursor() as cursor:
            query = """
                  SELECT SUM(amount)
                  FROM operations
                  WHERE family_id = %s AND operation_type_id = 1;
                  """
            cursor.execute(query, (family_id,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0

    @staticmethod
    def get_total_income_for_user(client_id):
        """Получение общей суммы доходов определённого пользователя."""
        with StatService._connection.cursor() as cursor:
            query = """
                SELECT SUM(amount)
                FROM operations
                WHERE client_id = %s AND operation_type_id = 1;
                """
            cursor.execute(query, (client_id,))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0

    @staticmethod
    def get_stat_family_operation(family_id: int):
        expenses = StatService.get_total_expenses_for_family(family_id)
        income = StatService.get_total_income_for_family(family_id)

        # Устанавливаем темную тему с повышенной контрастностью
        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Helvetica']
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams['axes.labelweight'] = 'bold'

        # Создаем объект Figure
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0A0A0A')
        fig.set_facecolor('#0A0A0A')

        # Данные для графика
        categories = ['ДОХОДЫ', 'РАСХОДЫ']
        values = [income, expenses]
        colors = ['#6FCF97', '#EB5757']

        # Создаем столбцы
        bars = ax.bar(categories, values, color=colors, width=0.7,
                      edgecolor='white', linewidth=1.5, alpha=0.95,
                      zorder=2)

        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:,.0f} ₽',
                    ha='center', va='bottom',
                    fontsize=13, fontweight='heavy',
                    color='white',
                    path_effects=[withStroke(linewidth=2, foreground='black')])

        # Настройка заголовка
        ax.set_title('ФИНАНСОВАЯ СТАТИСТИКА СЕМЬИ',
                     pad=20, fontsize=17, fontweight='heavy',
                     color='white')

        # Настройка подписи оси Y
        ax.set_ylabel('СУММА (РУБ)', labelpad=15, fontsize=13, color='white', fontweight='heavy')

        # Настройка границ
        for spine in ax.spines.values():
            spine.set_color('#444444')
            spine.set_linewidth(2)

        # Настройка сетки
        ax.grid(axis='y', color='#444444', linestyle=':', alpha=0.8)
        ax.set_axisbelow(True)

        # Настройка тиков
        ax.tick_params(axis='both', colors='white', labelsize=12, width=2)

        # Добавляем баланс
        balance = income - expenses
        balance_color = '#4CAF50' if balance >= 0 else '#FF6B6B'
        balance_text = f"Баланс: {balance:+,.0f} ₽"
        ax.text(0.95, 0.95, balance_text,
                transform=ax.transAxes,
                ha='right', va='top',
                fontsize=12, fontweight='bold',
                color=balance_color,
                bbox=dict(facecolor='#121212', edgecolor=balance_color, boxstyle='round,pad=0.5'))

        plt.tight_layout()

        # Сохраняем график в файл
        temp_file_family = "family_stats.png"
        fig.savefig(temp_file_family, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Закрываем фигуру после сохранения

        return temp_file_family

    @staticmethod
    def get_stat_familyUsers_operation(family_id: int):
        clients = StatService.get_client_for_family(family_id)

        if not clients:
            print("Нет данных о клиентах для этой семьи")
            return

        names = []
        incomes = []
        expenses = []

        for client in clients:
            names.append(client[1])
            income = float(StatService.get_total_income_for_user(client[0]))
            expense = float(StatService.get_total_expenses_for_user(client[0]))
            incomes.append(income)
            expenses.append(expense)

        # Сортируем данные по балансу
        sorted_data = sorted(zip(names, incomes, expenses),
                             key=lambda x: x[1] - x[2], reverse=True)
        names, incomes, expenses = zip(*sorted_data)

        # Внутренняя функция для построения частичного графика
        def plot_chunk(names_chunk, incomes_chunk, expenses_chunk, chunk_num, total_chunks):
            plt.style.use('dark_background')
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.sans-serif': ['Segoe UI', 'Arial', 'Helvetica'],
                'axes.titleweight': 'bold',
                'axes.labelweight': 'bold'
            })

            fig, ax = plt.subplots(figsize=(14, 6 + len(names_chunk) * 0.3), facecolor='#0A0A0A')
            fig.set_facecolor('#0A0A0A')

            x = np.arange(len(names_chunk))
            width = 0.35

            # Столбцы доходов и расходов
            bars_income = ax.bar(x - width / 2, incomes_chunk, width,
                                 label='Доходы', color='#6FCF97',
                                 edgecolor='white', linewidth=1.5, alpha=0.9)
            bars_expense = ax.bar(x + width / 2, expenses_chunk, width,
                                  label='Расходы', color='#EB5757',
                                  edgecolor='white', linewidth=1.5, alpha=0.9)

            # Подписи значений
            for bars in (bars_income, bars_expense):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{height:,.0f} ₽',
                            ha='center', va='bottom',
                            fontsize=11, fontweight='heavy',
                            color='white',
                            path_effects=[withStroke(linewidth=2, foreground='black')])

            # Баланс для каждого пользователя
            for i, (inc, exp) in enumerate(zip(incomes_chunk, expenses_chunk)):
                balance = inc - exp
                balance_color = '#4CAF50' if balance >= 0 else '#FF6B6B'
                ax.text(x[i], max(inc, exp) * 1.05, f"{balance:+,.0f} ₽",
                        ha='center', va='bottom',
                        fontsize=11, fontweight='bold',
                        color=balance_color,
                        bbox=dict(facecolor='#121212', edgecolor=balance_color, boxstyle='round,pad=0.3'))

            # Заголовок с номером части
            title = 'ФИНАНСОВАЯ СТАТИСТИКА ПО ЧЛЕНАМ СЕМЬИ'
            if total_chunks > 1:
                title += f' (Часть {chunk_num + 1} из {total_chunks})'
            ax.set_title(title, pad=25, fontsize=18, fontweight='heavy', color='white')

            ax.set_ylabel('СУММА (РУБ)', fontsize=14, color='white', fontweight='heavy')
            ax.set_xticks(x)
            ax.set_xticklabels([f"@{name}" for name in names_chunk],
                               fontsize=12, fontweight='bold', color='white')

            ax.legend(fontsize=12, framealpha=0.3, loc='upper right')
            ax.grid(axis='y', color='#444444', linestyle=':', alpha=0.5)

            for spine in ax.spines.values():
                spine.set_color('#444444')
                spine.set_linewidth(2)

            plt.tight_layout()

            # Сохраняем график в файл
            temp_file_users = f"users_stats_part_{chunk_num + 1}.png"
            fig.savefig(temp_file_users, dpi=300, bbox_inches='tight')
            plt.close(fig)  # Закрываем фигуру после сохранения

            return temp_file_users

        # Определяем размер группы и разбиваем данные
        chunk_size = 7
        total_users = len(names)

        if total_users <= chunk_size:
            # Если пользователей мало - один график
            return plot_chunk(names, incomes, expenses, 0, 1)
        else:
            # Разбиваем на группы по chunk_size пользователей
            total_chunks = (total_users + chunk_size - 1) // chunk_size
            temp_files = []
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = start_idx + chunk_size
                temp_files.append(plot_chunk(names[start_idx:end_idx],
                                             incomes[start_idx:end_idx],
                                             expenses[start_idx:end_idx],
                                             i, total_chunks))
            return temp_files

    @staticmethod
    def get_income_expense_time_series(family_id: int, start_date: str, end_date: str):
        """Получение данных и создание графика доходов/расходов по датам для семьи"""
        data = StatService.get_income_expense_by_date(family_id, start_date, end_date)
        return StatService._create_income_expense_time_series(
            data,
            title_prefix='Семейные финансы',
            period_info=f'{start_date} - {end_date}'
        )

    @staticmethod
    def get_client_info_by_tg_nick(tg_nick: str):
        """Получить всю информацию о клиенте по Telegram username"""
        try:
            with StatService._connection.cursor() as cursor:
                query = """
                           SELECT client_id, family_id
                           FROM clients
                           WHERE tg_nick = %s;
                       """
                cursor.execute(query, (tg_nick,))
                result = cursor.fetchone()
                if result:
                    return {
                        'client_id': result[0],
                        'family_id': result[1]
                    }
                return None
        except Exception as e:
            print(f"Ошибка при получении информации о клиенте: {e}")
            return None

    @staticmethod
    def get_client_income_expense_time_series(client_id: int, start_date: str, end_date: str):
        """Получение данных и создание графика доходов/расходов по датам для клиента"""
        data = StatService.get_client_income_expense_by_date(client_id, start_date, end_date)
        return StatService._create_income_expense_time_series(
            data,
            title_prefix='Личные финансы',
            period_info=f'{start_date} - {end_date}'
        )

    @staticmethod
    def get_stat_family_category_with_chart_by_date(family_id: int, start_date: str, end_date: str):
        """Визуализация статистики расходов семьи за период"""
        data = StatService.get_stat_family_category_by_date(family_id, start_date, end_date)
        return StatService._create_pie_chart(
            data,
            title_prefix='Расходы семьи',
            period_info=f'{start_date} - {end_date}'
        )

    @staticmethod
    def get_stat_client_category_with_chart_by_date(client_id: int, start_date: str, end_date: str):
        """Визуализация статистики расходов клиента за период"""
        data = StatService.get_stat_client_category_by_date(client_id, start_date, end_date)
        return StatService._create_pie_chart(
            data,
            title_prefix='Расходы клиента',
            period_info=f'{start_date} - {end_date}'
        )
