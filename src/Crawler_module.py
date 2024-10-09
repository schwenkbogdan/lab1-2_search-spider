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

                            # Save the link relationship from the current page to the external link
                            self.save_link_between_urls(page, external_link)

                        # Save the relationship for internal links as well
                        for internal_link in internal_links:
                            self.save_link_between_urls(page, internal_link)

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
                    self.save_link_between_urls(url, external_link)  # Save the link relationship
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

            # Write word list

            # Текст, слова, и их местоположение
            text = self.get_text_only(soup)

            words = self.separate_words(text)
            self.save_text_to_db(words)

            # Assuming `wordid` is retrieved from the saved words in the DB
            for word in words:
                wordid = self.get_word_id(word)  # You need to implement this method to get the word ID
                for link in unique_internal_links + unique_external_links:
                    linkid = self.get_link_id(link)  # You need to implement this method to get the link ID
                    if wordid is not None and linkid is not None:
                        self.save_link_words(wordid, linkid)  # Save the word-link relationship

            # Print found links
            print(
                f"Found {len(unique_internal_links)} internal links and {len(unique_external_links)} external links on {url}")
            return unique_internal_links, unique_external_links

        except Exception as e:
            print(f"Error: {e}")
            return [], []

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

        # Регулярное выражение для разделения по не-словам (любые символы, кроме букв и цифр)
        splitter = re.compile(r'\W+')
        cyrillic_pattern = re.compile(r'^[а-яА-ЯёЁ]+$')

        # Разделяем текст на слова и фильтруем ненужные
        return [
            s.lower() for s in splitter.split(text)
            if (cyrillic_pattern.match(s) and
                s.lower() not in self.stopwords and
                len(s) >= 3)  # Отбрасываем слова меньше 3 букв
        ]

    # 4. Проиндексирован ли URL (проверка наличия URL в БД)
    def is_indexed(self, url):
        """Проверка, проиндексирована ли страница"""
        return False

    def add_link(self, url_from, url_to, link_text):
        return ""

    # 5. Добавление ссылки с одной страницы на другую
    def add_link_ref(self, url_from, url_to, link_text):
        return ""

    def get_word_id(self, word):
        """Retrieve the word ID from the database based on the word."""
        self.cursor.execute('SELECT id FROM wordlist WHERE word = ?', (word,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_link_id(self, link):
        """Retrieve the link ID from the database based on the link."""
        self.cursor.execute('SELECT id FROM urllist WHERE url = ?', (link,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def save_link_words(self, wordid, linkid):
        """Saves the relationship between words and links to the linkwords table."""
        try:
            # Prepare the SQL insert statement
            self.cursor.execute(
                'INSERT INTO linkwords (wordid, linkid) VALUES (?, ?)',
                (wordid, linkid)
            )
            self.conn.commit()
            logging.info(f"Saved wordid {wordid} for linkid {linkid} in linkwords table.")
        except sqlite3.Error as e:
            logging.error(f"Error saving link-word relationship: {e}")
            print(f"Ошибка при записи связи между словом и ссылкой: {e}")

    def save_link_between_urls(self, from_url, to_url):
        """Saves the relationship between two URLs to the linkbetweenurl table."""
        try:
            # Get the ID of the from_url
            self.cursor.execute('SELECT id FROM urlList WHERE url = ?', (from_url,))
            from_url_id = self.cursor.fetchone()

            # Get the ID of the to_url
            self.cursor.execute('SELECT id FROM urlList WHERE url = ?', (to_url,))
            to_url_id = self.cursor.fetchone()

            if from_url_id and to_url_id:  # Check if both URLs exist in the database
                # Prepare the SQL insert statement using IDs
                self.cursor.execute(
                    'INSERT INTO linkBetweenURL (from_urlid, to_urlid) VALUES (?, ?)',
                    (from_url_id[0], to_url_id[0])  # Save IDs instead of URLs
                )
                self.conn.commit()
                logging.info(
                    f"Saved link from {from_url} (ID: {from_url_id[0]}) to {to_url} (ID: {to_url_id[0]}) in linkBetweenURL table.")
            # else:
            #     logging.warning(f"One of the URLs {from_url} or {to_url} does not exist in the database.")
        except sqlite3.Error as e:
            logging.error(f"Error saving link between URLs: {e}")
            print(f"Ошибка при записи связи между URL: {e}")

    def is_ignored_file(self, link):
        """Проверяет, является ли ссылка ссылкой на файл, который нужно игнорировать.
        Добавить игнор недопустимых ссылок"""
        ignored_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
                              '.pdf', '.zip', '.tar', '.gz', '.mp3', '.mp4',
                              '.avi', '.mov', '.mkv', '.exe')
        return link.lower().endswith(ignored_extensions)

    # 7. Инициализация таблиц в БД
    def init_db_from_file(self):
        """Инициализирует базу данных с помощью SQL-файла."""
        with open(self.schema_path, 'r') as sql_file:
            sql_script = sql_file.read()

        # Выполнение скрипта из SQL файла
        self.cursor.executescript(sql_script)
        self.conn.commit()

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

    def save_wordlocation_to_db(self, urlid, wordid, location):
        """Метод для записи позиции слова в базу данных"""
        try:
            # Создание значения для вставки
            values = (urlid, wordid, location)

            # Выполнение вставки с игнорированием дубликатов
            self.cursor.execute('INSERT OR IGNORE INTO wordlocation (urlid, wordid, location) VALUES (?, ?, ?)', values)
            self.conn.commit()
            logging.info(f"Saved word location for URL ID {urlid}, Word ID {wordid}, Location {location}")
            print("Записано")
        except sqlite3.Error as e:
            logging.error(f"Error saving word location: {e}")
            print(f"Ошибка при записи позиции слова: {e}")

    def load_config(self, config_file):
        """Метод для загрузки конфигурации из файла .ini."""
        config = configparser.ConfigParser()
        config.read(config_file)
        return config

    def load_stopwords(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stopwords = [line.strip().lower() for line in f if line.strip()]
            return stopwords
        except FileNotFoundError:
            print(f"Файл {file_path} не найден.")
            return []

    def laod_ignored_files(self):
        try:
            ignored = ''
        except FileNotFoundError:
            return []

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            logging.info("Database connection closed.")
            print("Соединение с базой данных закрыто.")
