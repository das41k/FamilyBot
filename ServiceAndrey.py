import datetime

from DBconnection import connection


class Part_Andrey:
    cursor = connection.cursor()

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
            Part_Andrey.cursor.execute(
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
    def get_categories_from_db():
        try:

            Part_Andrey.cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            categories = {row[1]: row[0] for row in Part_Andrey.cursor.fetchall()}  # Словарь {название: id}

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
            Part_Andrey.cursor.execute(query, (operation_name,))

            result = Part_Andrey.cursor.fetchone()

            if result:
                return result[0]  # Возвращаем operation_type_id
            return None

        except Exception as error:
            print(f"Ошибка при получении operation_type_id для '{operation_name}':", error)
            return None

    @staticmethod
    def save_user_to_db(username):
        try:
            # Проверяем, есть ли уже такой пользователь
            Part_Andrey.cursor.execute("SELECT client_id FROM clients WHERE tg_nick = %s", (username,))
            if Part_Andrey.cursor.fetchone():
                return True  # Пользователь уже существует

            # Добавляем нового пользователя
            Part_Andrey.cursor.execute(
                "INSERT INTO clients (tg_nick) VALUES (%s) RETURNING client_id",
                (username,)
            )
            connection.commit()
            return True

        except Exception as error:
            print("Ошибка при сохранении пользователя:", error)
            return False

    @staticmethod
    def get_client_id(username: str) -> int:
        """Получает client_id по username"""
        try:
            Part_Andrey.cursor.execute(
                "SELECT client_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = Part_Andrey.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении client_id: {e}")
            return None

    @staticmethod
    def create_family(family_name: str, join_code: str, creator_username: str) -> int:
        """Создает новую семью и добавляет создателя в нее"""
        try:
            # Создаем новую семью
            Part_Andrey.cursor.execute(
                "INSERT INTO families (family_name, join_code) VALUES (%s, %s) RETURNING family_id",
                (family_name, join_code)
            )
            family_id = Part_Andrey.cursor.fetchone()[0]

            # Обновляем family_id у создателя
            Part_Andrey.cursor.execute(
                "UPDATE clients SET family_id = %s WHERE tg_nick = %s",
                (family_id, creator_username)
            )

            connection.commit()
            return family_id

        except Exception as e:
            print(f"Ошибка при создании семьи: {e}")
            connection.rollback()
            return None

    @staticmethod
    def join_family(join_code: str, username: str) -> bool:
        """Добавляет пользователя в семью по коду присоединения"""
        try:
            # Находим семью по коду
            Part_Andrey.cursor.execute(
                "SELECT family_id FROM families WHERE join_code = %s",
                (join_code,)
            )
            result = Part_Andrey.cursor.fetchone()

            if not result:
                return False

            family_id = result[0]

            # Обновляем family_id у пользователя
            Part_Andrey.cursor.execute(
                "UPDATE clients SET family_id = %s WHERE tg_nick = %s",
                (family_id, username)
            )

            connection.commit()
            return True

        except Exception as e:
            print(f"Ошибка при присоединении к семье: {e}")
            connection.rollback()
            return False

    @staticmethod
    def get_family_id(username: str) -> int:
        """Получает family_id пользователя"""
        try:
            Part_Andrey.cursor.execute(
                "SELECT family_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = Part_Andrey.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении family_id: {e}")
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
            Part_Andrey.cursor.execute(
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

    @staticmethod
    def get_family_info(family_id: int) -> dict:
        """Получает информацию о семье по её ID"""
        try:
            # Получаем основную информацию о семье
            Part_Andrey.cursor.execute(
                """SELECT family_name
                   FROM families 
                   WHERE family_id = %s""",
                (family_id,)
            )
            family_data = Part_Andrey.cursor.fetchone()

            if not family_data:
                return None

            # Получаем количество участников
            Part_Andrey.cursor.execute(
                """SELECT COUNT(*) 
                   FROM clients 
                   WHERE family_id = %s""",
                (family_id,)
            )
            member_count = Part_Andrey.cursor.fetchone()[0]

            return {
                'family_name': family_data[0],
                'member_count': member_count
            }

        except Exception as e:
            print(f"Ошибка при получении информации о семье: {e}")
            return None

    @staticmethod
    def leave_family(username: str) -> bool:
        """Удаляет пользователя из семьи"""
        try:
            # Сначала получаем family_id пользователя
            query = "SELECT family_id FROM clients WHERE tg_nick = %s"
            Part_Andrey.cursor.execute(query, (username,))
            result = Part_Andrey.cursor.fetchone()

            if not result or not result[0]:
                return False  # Пользователь не в семье

            family_id = result[0]

            query = "UPDATE clients SET family_id = NULL WHERE tg_nick = %s"
            Part_Andrey.cursor.execute(query, (username,))
            connection.commit()

            # Проверяем, остались ли другие участники в семье
            query = "SELECT COUNT(*) FROM clients WHERE family_id = %s"
            Part_Andrey.cursor.execute(query, (family_id,))
            count = Part_Andrey.cursor.fetchone()[0]
            print(f"Остаток - {count}")  # Исправлено: использование f-строки

            connection.commit()

            if count == 0:
                # Если участников не осталось - удаляем семью
                query = "DELETE FROM families WHERE family_id = %s"
                Part_Andrey.cursor.execute(query, (family_id,))
                print(f"Семья {family_id} удалена, так как не осталось участников")
                connection.commit()

            return True

        except Exception as e:
            print(f"Ошибка при выходе из семьи: {e}")
            connection.rollback()
            return False

    @staticmethod
    def get_family_members(family_id: int) -> list:
        """Получает список участников семьи"""
        try:
            Part_Andrey.cursor.execute(
                """SELECT tg_nick 
                   FROM clients 
                   WHERE family_id = %s""",
                (family_id,)
            )
            return [row[0] for row in Part_Andrey.cursor.fetchall()]

        except Exception as e:
            print(f"Ошибка при получении участников семьи: {e}")
            return []

    @staticmethod
    def check_join_code_available(join_code: str) -> bool:
        """Проверяет, свободен ли код для использования"""
        try:
            query = "SELECT COUNT(*) FROM families WHERE join_code = %s"
            Part_Andrey.cursor.execute(query, (join_code,))
            return Part_Andrey.cursor.fetchone()[0] == 0
        except Exception as e:
            print(f"Ошибка при проверке кода: {e}")
            return False

