import sqlite3


def initDB(dbName):
    # Подключение к базе данных (создание файла базы данных, если он не существует)
    conn = sqlite3.connect(dbName)
    cursor = conn.cursor()

    # Создание таблицы для проиндексированных URL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urllist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE
        )
    ''')

    # Создание таблицы для списка всех проиндексированных слов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wordlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            is_filtered BOOLEAN
        )
    ''')

    # Создание таблицы для мест вхождения слов в документы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wordlocation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urlid INTEGER,
            wordid INTEGER,
            location INTEGER,
            FOREIGN KEY (urlid) REFERENCES urllist(id),
            FOREIGN KEY (wordid) REFERENCES wordlist(id)
        )
    ''')

    # Создание таблицы для хранения связей между URL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linkBetweenURL (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_urlid INTEGER,
            to_urlid INTEGER,
            FOREIGN KEY (from_urlid) REFERENCES urllist(id),
            FOREIGN KEY (to_urlid) REFERENCES urllist(id)
        )
    ''')

    # Создание таблицы для хранения слов, связанных с ссылками
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linkwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wordid INTEGER,
            linkid INTEGER,
            FOREIGN KEY (wordid) REFERENCES wordlist(id),
            FOREIGN KEY (linkid) REFERENCES linkBetweenURL(id)
        )
    ''')

    # Подтверждение изменений и закрытие подключения
    conn.commit()
    conn.close()



    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS urllist (id INTEGER PRIMARY KEY, url TEXT UNIQUE)''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS wordlist (id INTEGER PRIMARY KEY, word TEXT UNIQUE)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS wordlocation (id INTEGER PRIMARY KEY, urlid INTEGER, wordid INTEGER, location INTEGER)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS link (id INTEGER PRIMARY KEY, fromid INTEGER, toid INTEGER)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS linkwords (wordid INTEGER, linkid INTEGER)')
        self.conn.commit()
