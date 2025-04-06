from DBservice import DatabaseManager
from datetime import datetime, timedelta
import hashlib

def main():
    try:
        # 1. Добавляем тестовую семью
        family_name = "Семья Петровых"
        join_code = hashlib.sha256("secret_code123".encode()).digest()  # Хешируем код

        print("\n1. Добавляем семью:")
        family_id = DatabaseManager.add_family(family_name, join_code)
        if family_id:
            print(f"Успешно! ID семьи: {family_id}")
        else:
            print("Ошибка при добавлении семьи")
            return

        # 2. Добавляем клиента (с привязкой к семье и без)
        print("\n2. Добавляем клиентов:")
        client1_id = DatabaseManager.add_client("@petrov_ivan", family_id)
        client2_id = DatabaseManager.add_client("@sidorov")  # Без семьи

        if client1_id and client2_id:
            print(f"Клиенты добавлены с ID: {client1_id} и {client2_id}")
        else:
            print("Ошибка при добавлении клиентов")
            return

        # 3. Добавляем типы операций
        print("\n3. Добавляем типы операций:")
        income_type_id = DatabaseManager.add_operation_type("Доход")
        expense_type_id = DatabaseManager.add_operation_type("Расход")

        if income_type_id and expense_type_id:
            print(f"Типы операций добавлены с ID: доход - {income_type_id}, расход - {expense_type_id}")
        else:
            print("Ошибка при добавлении типов операций")
            return

        # 4. Добавляем категории
        print("\n4. Добавляем категории:")
        food_category_id = DatabaseManager.add_category("Еда")
        salary_category_id = DatabaseManager.add_category("Зарплата")
        transport_category_id = DatabaseManager.add_category("Транспорт")

        if food_category_id and salary_category_id and transport_category_id:
            print(
                f"Категории добавлены с ID: Еда - {food_category_id}, Зарплата - {salary_category_id}, Транспорт - {transport_category_id}")
        else:
            print("Ошибка при добавлении категорий")
            return

        print("\nВсе операции выполнены успешно!")

    except Exception as e:
        print(f"\n[CRITICAL] Произошла непредвиденная ошибка: {e}")
    finally:
        # В реальном приложении закрытие соединения лучше делать явно при завершении работы
        pass


if __name__ == "__main__":
    main()