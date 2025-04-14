import datetime

from DBconnection import connection


class family_service:
    cursor = connection.cursor()

    @staticmethod
    def get_client_id(username: str) -> int:
        """Получает client_id по username"""
        try:
            family_service.cursor.execute(
                "SELECT client_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = family_service.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении client_id: {e}")
            return None

    @staticmethod
    def create_family(family_name: str, join_code: str, creator_username: str) -> int:
        """Создает новую семью и добавляет создателя в нее"""
        try:
            # Создаем новую семью
            family_service.cursor.execute(
                "INSERT INTO families (family_name, join_code) VALUES (%s, %s) RETURNING family_id",
                (family_name, join_code)
            )
            family_id = family_service.cursor.fetchone()[0]

            # Обновляем family_id у создателя
            family_service.cursor.execute(
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
            family_service.cursor.execute(
                "SELECT family_id FROM families WHERE join_code = %s",
                (join_code,)
            )
            result = family_service.cursor.fetchone()

            if not result:
                return False

            family_id = result[0]

            # Обновляем family_id у пользователя
            family_service.cursor.execute(
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
            family_service.cursor.execute(
                "SELECT family_id FROM clients WHERE tg_nick = %s",
                (username,)
            )
            result = family_service.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении family_id: {e}")
            return None

    @staticmethod
    def get_family_info(family_id: int) -> dict:
        """Получает информацию о семье по её ID"""
        try:
            # Получаем основную информацию о семье
            family_service.cursor.execute(
                """SELECT family_name
                   FROM families 
                   WHERE family_id = %s""",
                (family_id,)
            )
            family_data = family_service.cursor.fetchone()

            if not family_data:
                return None

            # Получаем количество участников
            family_service.cursor.execute(
                """SELECT COUNT(*) 
                   FROM clients 
                   WHERE family_id = %s""",
                (family_id,)
            )
            member_count = family_service.cursor.fetchone()[0]

            return {
                'family_name': family_data[0],
                'member_count': member_count
            }

        except Exception as e:
            print(f"Ошибка при получении информации о семье: {e}")
            return None

    @staticmethod
    def leave_family(username: str) -> bool:
        """Удаляет пользователя из семьи, включая все связанные данные

        Args:
            username: Имя пользователя в Telegram

        Returns:
            bool: True если операция успешна, False если пользователь не в семье или произошла ошибка
        """
        try:
            # Получаем family_id пользователя
            query = "SELECT family_id FROM clients WHERE tg_nick = %s"
            family_service.cursor.execute(query, (username,))
            result = family_service.cursor.fetchone()

            if not result or not result[0]:
                return False  # Пользователь не в семье

            family_id = result[0]

            # Удаляем пользователя из семьи
            query = "UPDATE clients SET family_id = NULL WHERE tg_nick = %s"
            family_service.cursor.execute(query, (username,))
            connection.commit()

            # Проверяем, остались ли участники в семье
            query = "SELECT COUNT(*) FROM clients WHERE family_id = %s"
            family_service.cursor.execute(query, (family_id,))
            count = family_service.cursor.fetchone()[0]
            print(f"Осталось участников в семье: {count}")

            if count == 0:
                # Удаляем связанные записи из ВСЕХ зависимых таблиц
                tables_to_clear = [
                    "operations",
                    "recurringoperations"
                    # Добавьте сюда другие таблицы при необходимости
                ]

                for table in tables_to_clear:
                    try:
                        delete_query = f"DELETE FROM {table} WHERE family_id = %s"
                        family_service.cursor.execute(delete_query, (family_id,))
                        print(f"Удалены записи из {table} для семьи {family_id}")
                    except Exception as e:
                        print(f"Ошибка при очистке {table}: {e}")
                        connection.rollback()
                        return False

                # Удаляем саму семью
                delete_family_query = "DELETE FROM families WHERE family_id = %s"
                family_service.cursor.execute(delete_family_query, (family_id,))
                print(f"Семья {family_id} удалена, так как не осталось участников")
                connection.commit()

            return True

        except Exception as e:
            print(f"Ошибка при выходе из семьи: {e}")
            if 'connection' in globals():
                connection.rollback()
            return False
    @staticmethod
    def get_family_members(family_id: int) -> list:
        """Получает список участников семьи"""
        try:
            family_service.cursor.execute(
                """SELECT tg_nick 
                   FROM clients 
                   WHERE family_id = %s""",
                (family_id,)
            )
            return [row[0] for row in family_service.cursor.fetchall()]

        except Exception as e:
            print(f"Ошибка при получении участников семьи: {e}")
            return []


    @staticmethod
    def check_join_code_available(join_code: str) -> bool:
        """Проверяет, свободен ли код для использования"""
        try:
            query = "SELECT COUNT(*) FROM families WHERE join_code = %s"
            family_service.cursor.execute(query, (join_code,))
            return family_service.cursor.fetchone()[0] == 0
        except Exception as e:
            print(f"Ошибка при проверке кода: {e}")
            return False

    @staticmethod
    def get_join_code(family_id: int) -> str:
        """Получает код присоединения семьи и преобразует из bytea в строку"""
        try:
            family_service.cursor.execute("SELECT join_code FROM families WHERE family_id = %s",
                                          (family_id,))
            result = family_service.cursor.fetchone()
            if not result:
                return None
            # Преобразуем bytea в строку
            bytea_data = result[0]
            if isinstance(bytea_data, memoryview):
                bytea_data = bytes(bytea_data)
            if isinstance(bytea_data, bytes):
                try:  # Пытаемся декодировать как UTF-8 (если данные были строкой)
                    return bytea_data.decode('utf-8')
                except UnicodeDecodeError:
                    # Если не UTF-8, возвращаем hex представление
                    return bytea_data.hex()
            else:  # Если данные не bytes, возвращаем как есть
                return str(bytea_data)
        except Exception as e:
            print(f"Ошибка при получении кода присоединения: {e}")
        return None