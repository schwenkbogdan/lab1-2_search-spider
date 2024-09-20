import re
import os
import requests
import sqlite3
from logging import currentframe
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class Crawler:

    # 0. Конструктор Инициализация паука с параметрами БД
    def __init__(self, db_file_name):
        print("Конструктор")
        self.db_file_name = db_file_name
        self.conn = sqlite3.connect(db_file_name)
        self.cursor = self.conn.cursor()
        self.init_db()
        pass

    # 0. Деструктор
    def __del__(self):
        print("Деструктор")
        if self.conn:
            self.close_db()

    # 6. Непосредственно сам метод сбора данных.
    # Начиная с заданного списка страниц, выполняет поиск в ширину
    # до заданной глубины, индексируя все встречающиеся по пути страницы
    def crawl(self, start_url, depth=2):
        queue = [(start_url, 0)]  # Очередь ссылок для обхода

        while queue:
            url, current_depth = queue.pop(0)  # Извлекаем первую ссылку из очереди
            if current_depth > depth:
                continue

            print(f"Обход страницы: {url}")
            links = self.parse(url)  # Вызываем метод parse

            if links is None:  # Добавляем проверку, если parse вернул None
                continue

            # Сохраняем найденные ссылки в БД
            self.save_urls_to_db(links)

            # Добавляем новые ссылки в очередь для дальнейшего обхода
            for link in links:
                queue.append((link, current_depth + 1))

    # 7. Инициализация таблиц в БД
    def init_db(self):

        # Создание таблицы для проиндексированных URL
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS urllist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        ''')

        # Создание таблицы для списка всех проиндексированных слов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wordlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE,
                is_filtered BOOLEAN
            )
        ''')

        # Создание таблицы для мест вхождения слов в документы
        self.cursor.execute('''
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
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS linkBetweenURL (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_urlid INTEGER,
                to_urlid INTEGER,
                FOREIGN KEY (from_urlid) REFERENCES urllist(id),
                FOREIGN KEY (to_urlid) REFERENCES urllist(id)
            )
        ''')

        # Создание таблицы для хранения слов, связанных с ссылками
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS linkwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wordid INTEGER,
                linkid INTEGER,
                FOREIGN KEY (wordid) REFERENCES wordlist(id),
                FOREIGN KEY (linkid) REFERENCES linkBetweenURL(id)
            )
        ''')

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
        try:
            # Получаем HTML-контент страницы
            html_doc = requests.get(url)
            print(f"Попытка открыть страницу {url}")

            # Разбираем HTML-код
            soup = BeautifulSoup(html_doc.text, 'html.parser')

            # Удаляем ненужные теги (script, style)
            for tag in soup(['script', 'style']):
                tag.decompose()

            # Находим все ссылки на странице
            links = []
            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])  # Преобразуем относительные ссылки в абсолютные
                # Проверяем, что ссылка ведёт на тот же домен
                if urlparse(link).netloc == urlparse(url).netloc:
                    links.append(link)

            unique_links = list(set(links))  # Уникализируем ссылки

            print("\nНайденные ссылки на страницы этого сайта:")
            for link in unique_links:
                print(link)

            print(f"\nВсего найдено ссылок: {len(unique_links)}")

            return unique_links

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при попытке открыть {url}: {e}")
            return None

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("Соединение с базой данных закрыто.")
