import psycopg2
from DBconnection import connection


class DatabaseManager:
    cursor = connection.cursor()

    @staticmethod
    def add_family(family_name: str, join_code: bytes):
        """Добавление новой семьи"""
        try:
            query = """
                    INSERT INTO Families (family_name, join_code)
                    VALUES (%s, %s)
                    RETURNING family_id
                """
            DatabaseManager.cursor.execute(query, (family_name, join_code))
            family_id = DatabaseManager.cursor.fetchone()[0]
            connection.commit()
            print(f"[INFO] Семья '{family_name}' добавлена с ID: {family_id}")
            return family_id
        except Exception as _ex:
            print("[ERROR] Ошибка при добавлении семьи:", _ex)

    @staticmethod
    def add_client(tg_nick: str, family_id: int = None):
        """Добавление нового клиента"""
        try:
            query = """
                    INSERT INTO Clients (tg_nick, family_id)
                    VALUES (%s, %s)
                    RETURNING client_id
                """
            DatabaseManager.cursor.execute(query, (tg_nick, family_id))
            client_id = DatabaseManager.cursor.fetchone()[0]
            connection.commit()
            print(f"[INFO] Клиент '{tg_nick}' добавлен с ID: {client_id}")
            return client_id
        except Exception as _ex:
            print("[ERROR] Ошибка при добавлении клиента:", _ex)

    @staticmethod
    def add_operation_type(name: str):
        """Добавление типа операции"""
        try:
            query = """
                    INSERT INTO OperationTypes (name)
                    VALUES (%s)
                    RETURNING operation_type_id
                """
            DatabaseManager.cursor.execute(query, (name,))
            type_id = DatabaseManager.cursor.fetchone()[0]
            connection.commit()
            print(f"[INFO] Тип операции '{name}' добавлен с ID: {type_id}")
            return type_id
        except Exception as _ex:
            print("[ERROR] Ошибка при добавлении типа операции:", _ex)

    @staticmethod
    def add_category(category_name: str):
        """Добавление категории"""
        try:
            query = """
                    INSERT INTO Categories (category_name)
                    VALUES (%s)
                    RETURNING category_id
                """
            DatabaseManager.cursor.execute(query, (category_name,))
            category_id = DatabaseManager.cursor.fetchone()[0]
            connection.commit()
            print(f"[INFO] Категория '{category_name}' добавлена с ID: {category_id}")
            return category_id
        except Exception as _ex:
            print("[ERROR] Ошибка при добавлении категории:", _ex)