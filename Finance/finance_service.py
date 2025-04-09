from DBconnection import connection
from datetime import datetime
import datetime

class FinanceService:
    cursor = connection.cursor()
    @staticmethod
    def get_categories_from_db():
        try:

            FinanceService.cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            categories = {row[1]: row[0] for row in FinanceService.cursor.fetchall()}  # Словарь {название: id}

            return categories

        except Exception as error:
            print("Ошибка при работе с PostgreSQL:", error)
            return {"Еда": 1, "Транспорт": 2, "Жилье": 3}  # Категории по умолчанию при ошибке

    @staticmethod
    def get_operation_type_id_from_db(operation_name: str):
        """
        Получает ID типа операции по его названию из таблицы operationtypes

        :param operation_name: Название типа операции (например, 'расход' или 'доход')
        :return: ID операции или None при ошибке
        """
        try:
            query = "SELECT operation_type_id, name FROM operationtypes WHERE name = %s"
            FinanceService.cursor.execute(query, (operation_name,))

            result = FinanceService.cursor.fetchone()

            if result:
                return result[0]  # Возвращаем operation_type_id
            return None

        except Exception as error:
            print(f"Ошибка при получении operation_type_id для '{operation_name}':", error)
            return None

    @staticmethod
    def add_operation(amount: float, operation_date: datetime.datetime,
                      category_id: int, operation_type_id: int,
                      client_id: int, family_id: int = None):
        """Добавляет операцию (доход или расход)"""
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
            print(f"[INFO] Добавлена операция для client_id {client_id}")

        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении операции: {e}")
            connection.rollback()
            raise

    @staticmethod
    def get_family_id(username: str) -> int:
        """Получает family_id пользователя"""
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
    def get_client_id(username: str) -> int:
        """Получает client_id по username"""
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
    def add_recurring_operation(amount: float, operation_type_id: int,
                                category_id: int, client_id: int,
                                date_start: datetime.date, date_end: datetime.date,
                                payment_interval: str, family_id: int = None):
        """Добавляет постоянную операцию (доход/расход)"""
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
            print(f"[INFO] Добавлена постоянная операция для client_id {client_id}")

        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении постоянной операции: {e}")
            connection.rollback()
            raise