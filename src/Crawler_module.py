import bs4
import requests
import sqlite3
import re
from logging import currentframe
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup




def save_url_to_db111(cursor, url):
    try:
        # Вставляем URL в таблицу, если его еще нет
        cursor.execute('INSERT OR IGNORE INTO urllist (url) VALUES (?)', (url,))
    except sqlite3.Error as e:
        print(f"Ошибка при записи URL {url}: {e}")


class Crawler:

    # 0. Конструктор Инициализация паука с параметрами БД
    def __init__(self, db_file_name):
        print("Конструктор")
        self.conn = sqlite3.connect(db_file_name)
        self.cursor = self.conn.cursor()
        self.init_db()
        pass

    # 0. Деструктор
    def __del__(self):
        print("Деструктор")
        self.close_db()
        pass

    def get_entry_id(self, table, field, value, createnew=True):
        self.cursor.execute(f"SELECT id FROM {table} WHERE {field} = ?", (value,))
        res = self.cursor.fetchone()
        if res is None:
            if createnew:
                self.cursor.execute(f"INSERT INTO {table} ({field}) VALUES (?)", (value,))
                self.conn.commit()
                return self.cursor.lastrowid
            else:
                return None
        else:
            return res[0]

    # 1. Индексирование одной страницы
    def add_index(self, soup, url):
        if self.is_indexed(url):
            return
        print(f"Индексация {url}")

        # Вставляем URL в таблицу urllist
        urlid = self.get_entry_id('urllist', 'url', url)

        # Разбираем текст на слова
        text = self.get_text_only(soup)
        words = self.separate_words(text)

        # Добавляем местоположение каждого слова в таблицу wordlocation
        for i, word in enumerate(words):
            wordid = self.get_entry_id('wordlist', 'word', word)
            self.cursor.execute("INSERT INTO wordlocation (urlid, wordid, location) VALUES (?, ?, ?)",
                                (urlid, wordid, i))
        self.conn.commit()

    def add_to_index(self, url, soup):
        """Индексирует страницу, если она еще не проиндексирована"""
        if self.is_indexed(url):
            return
        print(f"Индексация {url}")

        # Извлечение всех слов из текста страницы
        text = self.get_text_only(soup)
        words = self.separate_words(text)

        # Получаем идентификатор страницы для вставки в таблицу wordlocation
        urlid = self.get_entry_id('urllist', 'url', url)

        # Индексируем каждое слово
        for i, word in enumerate(words):
            if len(word) > 2:  # Простейший фильтр слов
                wordid = self.get_entry_id('wordlist', 'word', word)
                self.cursor.execute("INSERT INTO wordlocation (urlid, wordid, location) VALUES (?, ?, ?)",
                                    (urlid, wordid, i))
        self.conn.commit()

    # 2. Получение текста страницы
    def get_text_only(self, soup):
        # Извлекаем текст из тегов
        return soup.get_text()

    # 3. Разбиение текста на слова
    def separate_words(self, text):
        """Разделение текста на слова с простейшей фильтрацией"""
        import re
        splitter = re.compile(r'\W+')  # Делим по не-словам
        return [s.lower() for s in splitter.split(text) if s != '']

    # 4. Проиндексирован ли URL (проверка наличия URL в БД)
    def is_indexed(self, url):
        """Проверка, проиндексирована ли страница"""
        self.cursor.execute("SELECT id FROM urllist WHERE url=?", (url,))
        result = self.cursor.fetchone()
        if result is not None:
            # Проверка, проиндексированы ли слова
            self.cursor.execute("SELECT * FROM wordlocation WHERE urlid=?", (result[0],))
            if self.cursor.fetchone() is not None:
                return True
        return False

    def add_link(self, url_from, url_to, link_text):
        fromid = self.get_entry_id('urllist', 'url', url_from)
        toid = self.get_entry_id('urllist', 'url', url_to)

        # Добавляем запись о ссылке в таблицу link и получаем ID вставленной ссылки
        self.cursor.execute("INSERT INTO link (fromid, toid) VALUES (?, ?)", (fromid, toid))
        linkid = self.cursor.lastrowid

        # Разбиваем текст ссылки на слова и добавляем их в таблицу linkwords
        words = self.separate_words(link_text)
        for word in words:
            wordid = self.get_entry_id('wordlist', 'word', word)
            self.cursor.execute("INSERT INTO linkwords (wordid, linkid) VALUES (?, ?)", (wordid, linkid))
        self.conn.commit()

    # 5. Добавление ссылки с одной страницы на другую
    def add_link_ref(self, url_from, url_to, link_text):
        # Получаем идентификаторы URL (если их нет в таблице urllist, они будут добавлены)
        fromid = self.get_entry_id('urllist', 'url', url_from)
        toid = self.get_entry_id('urllist', 'url', url_to)

        # Проверяем, существует ли уже такая ссылка
        self.cursor.execute("SELECT id FROM link WHERE fromid=? AND toid=?", (fromid, toid))
        res = self.cursor.fetchone()

        if res is None:
            # Если записи нет, добавляем её в таблицу link
            self.cursor.execute("INSERT INTO link (fromid, toid) VALUES (?, ?)", (fromid, toid))
            linkid = self.cursor.lastrowid

            # Добавляем слова из текста ссылки в таблицу linkwords
            words = self.separate_words(link_text)
            for word in words:
                wordid = self.get_entry_id('wordlist', 'word', word)
                self.cursor.execute("INSERT INTO linkwords (wordid, linkid) VALUES (?, ?)", (wordid, linkid))
            self.conn.commit()
        else:
            print(f"Link from {url_from} to {url_to} уже существует.")

    # 6. Непосредственно сам метод сбора данных.
    # Начиная с заданного списка страниц, выполняет поиск в ширину
    # до заданной глубины, индексируя все встречающиеся по пути страницы
    def crawl(self, url_list, depth):
        """Основной метод для обхода страниц и индексации"""
        current_depth = 0
        pages_to_crawl = url_list

        while current_depth <= depth and pages_to_crawl:
            new_pages = []
            for page in pages_to_crawl:
                if not self.is_indexed(page):
                    try:
                        print("Получить и проанализировать страницу")
                        # Получить и проанализировать страницу
                        links = self.parse(page)
                        self.save_urls_to_db(links)


                    except Exception as e:
                        print(f"Ошибка при обработке {page}: {e}")

            # Обновляем список страниц для следующей глубины
            pages_to_crawl = list(set(new_pages))  # Убираем дубликаты
            current_depth += 1

    # 7. Инициализация таблиц в БД
    def init_db(self):
        # Создание таблицы urllist, если она не существует
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS urllist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        ''')
        self.conn.commit()
        print("бд создана")

    # 8. Вспомогательная функция для получения идентификатора и
    # добавления записи, если такой еще нет
    def get_entry_id(self, table_name, field_name, value):
        return 1

    # Метод для записи уникального URL в базу данных
    def save_urls_to_db(self, urls):
        try:
            # Создание списка значений для вставки
            values = [(url,) for url in set(urls)]  # Используем set для удаления дубликатов
            # Выполнение вставки с игнорированием дубликатов
            self.cursor.executemany('INSERT OR IGNORE INTO urllist (url) VALUES (?)', values)
            self.conn.commit()
            print("Записано")
        except sqlite3.Error as e:
            print(f"Ошибка при записи URL: {e}")

    def parse(self, url):
        """Получает список адресов для поиска в них уникальных страниц на том же адресе и подсчёта их количества, отдаёт лист найденных страниц"""
        try:
            # Получить HTML код страницы
            html_doc = requests.get(url)
            print(f"6. crawl - Попытка открыть страницу {url}")

            # Разбор HTML-кода
            soup = BeautifulSoup(html_doc.text, 'html.parser')

            # Удалить ненужные элементы (script, style)
            for tag in soup(['script', 'style']):
                tag.decompose()

            # Найти все ссылки на странице
            links = []
            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])  # Создать абсолютную ссылку
                # Проверяем, чтобы ссылка вела на тот же домен
                if urlparse(link).netloc == urlparse(url).netloc:
                    links.append(link)

            # Уникализируем ссылки
            unique_links = list(set(links))

            # Вывести список ссылок и их количество
            print("\nНайденные ссылки на страницы этого сайта:")
            for link in unique_links:
                print(link)

            print(f"\nВсего найдено ссылок: {len(unique_links)}")

            return unique_links

        except Exception as e:
            print(f"Ошибка: {e}")
            print(f"Не могу открыть {url}")

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("Соединение с базой данных закрыто.")
