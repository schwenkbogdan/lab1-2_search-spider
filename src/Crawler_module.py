import re
# import os
import requests
import sqlite3
# from logging import currentframe
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
import configparser


class Crawler:

    # 0. Конструктор Инициализация паука с параметрами БД
    def __init__(self, db_file_name, config_file='config.ini'):
        print("Конструктор")
        self.config = self.load_config(config_file)
        # Чтение пути из конфигурации
        stopwords_file = self.config.get('paths', 'stopwords_file')
        # Получение параметров базы данных из конфигурации
        self.db_name = self.config['database']['db_name']
        self.schema_path = self.config['database']['schema_path']
        # Загружаем стоп-слова
        self.stopwords = self.load_stopwords(stopwords_file)
        self.db_file_name = db_file_name
        self.conn = sqlite3.connect(db_file_name)
        self.cursor = self.conn.cursor()
        self.init_db_from_file()
        pass

    # 0. Деструктор
    def __del__(self):
        print("Деструктор")
        if self.conn:
            self.close_db()

    # 6. Непосредственно сам метод сбора данных.
    # Начиная с заданного списка страниц, выполняет поиск в ширину
    # до заданной глубины, индексируя все встречающиеся по пути страницы
    def crawl(self, url_list, max_depth):
        """Crawls the site, indexing internal and external links recursively up to a specified depth"""
        self.save_urls_to_db(url_list)  # Save initial URLs to the DB
        crawled_urls = set()  # To keep track of already crawled URLs
        current_depth = 0
        pages_to_crawl = url_list  # Pages to be crawled at the current depth

        while current_depth <= max_depth and pages_to_crawl:
            new_pages = []  # To store new internal and external pages found at this depth

            for page in pages_to_crawl:
                if page not in crawled_urls and not self.is_indexed(page):
                    try:
                        print(f"Crawling page: {page}")
                        # Parse the page, separating internal and external links
                        internal_links, external_links = self.parse(page)

                        # Save internal links to the DB
                        self.save_urls_to_db(internal_links)
                        crawled_urls.add(page)  # Mark the current page as crawled

                        # Add internal links to be crawled in the next round
                        new_pages.extend(internal_links)

                        # Recursively crawl external links, respecting max_depth
                        for external_link in external_links:
                            self.crawl_external(external_link, 1, max_depth)

                    except Exception as e:
                        print(f"Error processing {page}: {e}")

            # Move to the next depth and remove duplicates
            pages_to_crawl = list(set(new_pages) - crawled_urls)
            current_depth += 1

        print(f"Crawl finished. Total unique URLs crawled: {len(crawled_urls)} at depth: {current_depth}")

    def crawl_external(self, url, current_depth, max_depth):
        """Recursively crawl external links, respecting the depth limit"""
        if current_depth > max_depth:
            return

        if not self.is_indexed(url):
            try:
                print(f"Recursively crawling external link: {url} at depth {current_depth}")
                _, external_links = self.parse(url)  # Only interested in external links
                self.save_urls_to_db([url])  # Save external link

                # Recursively crawl further external links
                for external_link in external_links:
                    self.crawl_external(external_link, current_depth + 1, max_depth)

            except Exception as e:
                print(f"Error processing external link {url}: {e}")

    def parse(self, url):
        """Parses a page and returns internal and external links separately"""
        try:
            # Fetch the HTML content of the page
            response = requests.get(url)
            print(f"Fetching page: {url}")

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted tags (like script, style)
            for tag in soup(['script', 'style']):
                tag.decompose()

            # Extract internal and external links separately
            internal_links = []
            external_links = []
            base_domain = urlparse(url).netloc  # Get the domain of the base URL

            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])  # Convert relative URLs to absolute URLs

                # Check if the link is internal or external
                if urlparse(link).netloc == base_domain:
                    if not self.is_ignored_file(link):  # Ignore links to files like images, PDFs, etc.
                        internal_links.append(link)
                else:
                    external_links.append(link)

            # Remove duplicates from both lists
            unique_internal_links = list(set(internal_links))
            unique_external_links = list(set(external_links))

            # Print found links
            print(
                f"Found {len(unique_internal_links)} internal links and {len(unique_external_links)} external links on {url}")
            return unique_internal_links, unique_external_links

        except Exception as e:
            print(f"Error: {e}")
            return [], []

    # 7. Инициализация таблиц в БД

    def init_db_from_file(self):
        """Инициализирует базу данных с помощью SQL-файла."""
        with open(self.schema_path, 'r') as sql_file:
            sql_script = sql_file.read()

        # Выполнение скрипта из SQL файла
        self.cursor.executescript(sql_script)
        self.conn.commit()

    # 8. Вспомогательная функция для получения идентификатора и
    # добавления записи, если такой еще нет
    def get_entry_id(self, table_name, field_name, value):
        return 1

    # 1. Индексирование одной страницы
    def add_index(self, soup, url):
        print(f"Индексация {url}")

    def add_to_index(self, url, soup):
        """Индексирует страницу, если она еще не проиндексирована"""
        if self.is_indexed(url):
            return
        print(f"Индексация {url}")

    # 2. Получение текста страницы
    def get_text_only(self, soup):
        # Извлекаем текст из тегов
        print("Извлекаем текст из тегов")
        return soup.get_text()

    # 3. Разбиение текста на слова
    def separate_words(self, text):
        """Разделение текста на слова с простейшей фильтрацией: удалить союзы, знаки препинания и ненужные слова."""
        import re
        # Регулярное выражение для разделения по не-словам (любые символы, кроме букв и цифр)
        splitter = re.compile(r'\W+')

        # Список слов, которые необходимо удалить (союзы и предлоги)
        not_allowed_word_list = [
            'я', 'и', 'но', 'или', 'что', 'как', 'а', 'с', 'на', 'в', 'под', 'за', 'к', 'у', 'по', 'до',
            'от', 'при', 'то', 'о'
                               'and', 'but', 'or', 'that', 'as', 'while', 'for', 'with', 'on', 'in', 'under', 'after',
            'to',
            'by', 'before'
        ]

        # Разделяем текст на слова и фильтруем ненужные
        return [s.lower() for s in splitter.split(text) if s.lower() not in not_allowed_word_list and s != '']

    def load_stopwords(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stopwords = [line.strip().lower() for line in f if line.strip()]
            return stopwords
        except FileNotFoundError:
            print(f"Файл {file_path} не найден.")
            return []

    # 4. Проиндексирован ли URL (проверка наличия URL в БД)
    def is_indexed(self, url):
        """Проверка, проиндексирована ли страница"""
        return False

    def add_link(self, url_from, url_to, link_text):
        return ""

    # 5. Добавление ссылки с одной страницы на другую
    def add_link_ref(self, url_from, url_to, link_text):
        return ""

    def is_ignored_file(self, link):
        """Проверяет, является ли ссылка ссылкой на файл, который нужно игнорировать.
        Добавить игнор недопустимых ссылок"""
        ignored_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
                              '.pdf', '.zip', '.tar', '.gz', '.mp3', '.mp4',
                              '.avi', '.mov', '.mkv', '.exe')
        return link.lower().endswith(ignored_extensions)

    def save_text_to_db(self, text):
        try:
            values = [(word,) for word in set(text)]  # Создаем список кортежей
            self.cursor.executemany('INSERT OR IGNORE INTO wordlist (word) VALUES (?)', values)
            self.conn.commit()

        except sqlite3.Error as e:
            logging.error(f"Error saving words: {e}")
            print(f"Ошибка при записи слов: {e}")

    def save_urls_to_db(self, urls):
        """Метод для записи уникального URL в базу данных"""
        try:
            # Создание списка значений для вставки
            values = [(url,) for url in set(urls)]  # Используем set для удаления дубликатов
            # Выполнение вставки с игнорированием дубликатов
            self.cursor.executemany('INSERT OR IGNORE INTO urllist (url) VALUES (?)', values)
            self.conn.commit()
            logging.info(f"URLs saved to the database: {len(urls)}")
            print("Записано")
        except sqlite3.Error as e:
            logging.error(f"Error saving URLs: {e}")
            print(f"Ошибка при записи URL: {e}")

    def load_config(self, config_file):
        """Метод для загрузки конфигурации из файла .ini."""
        config = configparser.ConfigParser()
        config.read(config_file)
        return config

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            logging.info("Database connection closed.")
            print("Соединение с базой данных закрыто.")
