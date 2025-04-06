import psycopg2
from config import host, user, password, db_name

try:
    # connection database
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    print("[INFO] Удачное подключение к БД")
    pass
except Exception as _ex:
    print("[WARNING] Ошибка работы PostgreSQL")
finally:
    pass