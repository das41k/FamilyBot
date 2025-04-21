from DBconnection import connection
from datetime import datetime

class FinanceService:
    cursor = connection.cursor()

    @staticmethod
    def get_categories_from_db():
        """Получает все категории расходов из базы данных"""
        try:
            FinanceService.cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            categories = {row[1]: row[0] for row in FinanceService.cursor.fetchall()}
            return categories
        except Exception as error:
            print("Ошибка при получении категорий из PostgreSQL:", error)
            return {}

    @staticmethod
    def get_category_name_by_id(category_id):
        """Получает название категории по ID"""
        try:
            FinanceService.cursor.execute(
                "SELECT category_name FROM categories WHERE category_id = %s",
                (category_id,)
            )
            result = FinanceService.cursor.fetchone()
            return result[0] if result else "Неизвестная категория"
        except Exception as error:
            print(f"Ошибка при получении названия категории {category_id}:", error)
            return "Неизвестная категория"

    @staticmethod
    def get_operation_type_id_from_db(operation_name):
        """Получает ID типа операции (доход/расход)"""
        try:
            query = "SELECT operation_type_id FROM operationtypes WHERE name = %s"
            FinanceService.cursor.execute(query, (operation_name,))
            result = FinanceService.cursor.fetchone()
            return result[0] if result else None
        except Exception as error:
            print(f"Ошибка при получении ID операции '{operation_name}':", error)
            return None

    @staticmethod
    def add_operation(amount, operation_date, category_id, operation_type_id, client_id, family_id=None):
        """Добавляет финансовую операцию в базу данных"""
        try:
            query = """
                INSERT INTO operations (
                    amount, operation_date, category_id,
                    operation_type_id, client_id, family_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            FinanceService.cursor.execute(
                query,
                (amount, operation_date, category_id,
                 operation_type_id, client_id, family_id)
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении операции: {e}")
            connection.rollback()
            return False

    @staticmethod
    def get_client_id(username):
        """Получает ID клиента по Telegram username"""
        try:
            FinanceService.cursor.execute(
                "SELECT client_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = FinanceService.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении client_id: {e}")
            return None

    @staticmethod
    def get_family_id(username):
        """Получает ID семьи клиента"""
        try:
            FinanceService.cursor.execute(
                "SELECT family_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = FinanceService.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении family_id: {e}")
            return None

    @staticmethod
    def add_recurring_operation(amount, operation_type_id, category_id, client_id,
                                date_start, date_end, payment_interval, family_id=None):
        """Добавляет повторяющуюся операцию"""
        try:
            query = """
                    INSERT INTO recurringoperations (
                        amount, operation_type_id, category_id,
                        client_id, family_id, date_start,
                        date_end, payment_interval
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
            FinanceService.cursor.execute(
                query,
                (amount, operation_type_id, category_id,
                 client_id, family_id, date_start,
                 date_end, payment_interval)
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении повторяющейся операции: {e}")
            connection.rollback()
            return False