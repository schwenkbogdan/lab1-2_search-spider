import sqlite3

def run_sql_script(db_name, script_file):
    # Открываем файл и считываем SQL-запросы
    with open(script_file, 'r') as file:
        sql_script = file.read()

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Выполняем SQL-запросы
        cursor.executescript(sql_script)
        conn.commit()
        print(f"Миграция успешно выполнена для базы данных '{db_name}'.")
    except Exception as e:
        print(f"Ошибка выполнения миграции: {e}")
    finally:
        conn.close()
