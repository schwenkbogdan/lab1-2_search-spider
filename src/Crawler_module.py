import re
import requests
import sqlite3
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
import configparser


class Crawler:

    def __init__(self, config_file='config.ini'):
        self.config = self.load_config(config_file)
        stopwords_file = self.config['paths']['stopwords_file']
        ignored_extensions_file = self.config['paths']['ignored_extensions_file']
        ignored_domains_file = self.config['paths']['ignored_domains_file']

        try:
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                self.stopwords = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Файл {stopwords_file} не найден.")
            self.stopwords = []

        try:
            with open(ignored_extensions_file, 'r', encoding='utf-8') as f:
                self.ignored_extentions = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Файл {ignored_extensions_file} не найден.")
            self.ignored_extentions = []

        try:
            with open(ignored_domains_file, 'r', encoding='utf-8') as f:
                self.ignored_domains = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Файл {ignored_domains_file} не найден.")
            self.ignored_domains = []
        self.db_file_name = self.config['database']['db_name']
        self.schema_path = self.config['database']['schema_path']
        self.conn = sqlite3.connect(self.db_file_name)
        self.cursor = self.conn.cursor()
        self.init_db_from_file()

    def __del__(self):
        print("Деструктор")
        if self.conn:
            self.close_db()

    def crawl(self, url_list, max_depth):
        self.save_urls_to_db(url_list)
        crawled_urls = set()
        current_depth = 0
        pages_to_crawl = url_list

        while current_depth <= max_depth and pages_to_crawl:
            new_pages = []
            for page in pages_to_crawl:
                if page not in crawled_urls and not self.is_indexed(page):
                    try:
                        print(f"Crawling page: {page}")
                        internal_links, external_links = self.parse(page)
                        self.save_urls_to_db(internal_links)
                        crawled_urls.add(page)
                        new_pages.extend(internal_links)

                        for external_link in external_links:
                            self.crawl_external(external_link, 1, max_depth)
                            self.save_link_between_urls_to_db(page, external_link)

                        for internal_link in internal_links:
                            self.save_link_between_urls_to_db(page, internal_link)

                    except Exception as e:
                        print(f"Error processing {page}: {e}")

            pages_to_crawl = list(set(new_pages) - crawled_urls)
            current_depth += 1

        print(f"Crawl finished. Total unique URLs crawled: {len(crawled_urls)} at depth: {current_depth}")

    def crawl_external(self, url, current_depth, max_depth):
        if current_depth > max_depth:
            return

        if not self.is_indexed(url):
            try:
                print(f"Recursively crawling external link: {url} at depth {current_depth}")
                _, external_links = self.parse(url)
                self.save_urls_to_db([url])

                for external_link in external_links:
                    self.save_link_between_urls_to_db(url, external_link)
                    self.crawl_external(external_link, current_depth + 1, max_depth)

            except Exception as e:
                print(f"Error processing external link {url}: {e}")

    def parse(self, url):
        try:
            response = requests.get(url)
            print(f"Fetching page: {url}")
            soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style']):
                tag.decompose()

            internal_links = []
            external_links = []
            base_domain = urlparse(url).netloc

            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])

                if urlparse(link).netloc == base_domain:
                    if not self.is_ignored_file(link):  # Исправлено использование метода
                        internal_links.append(link)
                else:
                    external_links.append(link)

            unique_internal_links = list(set(internal_links))
            unique_external_links = list(set(external_links))

            text = self.get_text_only(soup)
            words = self.separate_words(text)
            self.save_text_to_db(words)

            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])
                link_text = a_tag.get_text()
                linkid = self.get_link_id(link)

                if linkid is not None:
                    anchor_words = self.separate_words(link_text)
                    for word in anchor_words:
                        wordid = self.get_word_id(word)
                        if wordid is not None:
                            self.save_link_words_to_db(wordid, linkid)

            print(
                f"Found {len(unique_internal_links)} internal links and {len(unique_external_links)} external links on {url}")
            return unique_internal_links, unique_external_links

        except Exception as e:
            print(f"Error: {e}")
            return [], []

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

    def get_text_only(self, soup):
        # Извлекаем текст из тегов
        print("Извлекаем текст из тегов")
        return soup.get_text()

    def is_indexed(self, url):
        """Проверка, проиндексирована ли страница"""
        return False

    def is_ignored_file(self, link):
        """
        Проверяет, является ли файл игнорируемым на основе его расширения.
        """
        return any(link.lower().endswith(ext) for ext in self.ignored_extentions)

    def load_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        return config

    def load_file(self, file_path):
        """Загружает содержимое файла и возвращает список строк."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Файл {file_path} не найден.")
            return []

    def init_db_from_file(self):
        """Инициализирует базу данных с помощью SQL-файла."""
        with open(self.schema_path, 'r') as sql_file:
            sql_script = sql_file.read()

        self.cursor.executescript(sql_script)
        self.conn.commit()

    def get_link_id(self, link):
        """Retrieve the link ID from the database based on the link."""
        self.cursor.execute('SELECT id FROM urllist WHERE url = ?', (link,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_word_id(self, word):
        """Retrieve the word ID from the database based on the word."""
        self.cursor.execute('SELECT id FROM wordlist WHERE word = ?', (word,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def save_link_words_to_db(self, wordid, linkid):
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

    def save_link_between_urls_to_db(self, from_url, to_url):
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

    def save_wordlocation_to_db(self, urlid, wordid, location):
        try:
            values = (urlid, wordid, location)
            self.cursor.execute('INSERT OR IGNORE INTO wordlocation (urlid, wordid, location) VALUES (?, ?, ?)', values)
            self.conn.commit()
            logging.info(f"Saved word location for URL ID {urlid}, Word ID {wordid}, Location {location}")
        except sqlite3.Error as e:
            logging.error(f"Error saving word location: {e}")
            print(f"Ошибка при записи позиции слова: {e}")

    def save_urls_to_db(self, urls):
        try:
            values = [(url,) for url in set(urls)]
            self.cursor.executemany('INSERT OR IGNORE INTO urllist (url) VALUES (?)', values)
            self.conn.commit()
            logging.info(f"URLs saved to the database: {len(urls)}")
        except sqlite3.Error as e:
            logging.error(f"Error saving URLs: {e}")
            print(f"Ошибка при записи URL: {e}")

    def save_text_to_db(self, text):
        try:
            values = [(word,) for word in set(text)]
            self.cursor.executemany('INSERT OR IGNORE INTO wordlist (word) VALUES (?)', values)
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error saving words: {e}")
            print(f"Ошибка при записи слов: {e}")

    def close_db(self):
        """Закрывает соединение с базой данных, если оно открыто."""
        if self.conn:
            self.conn.close()
            print("Соединение с базой данных закрыто.")
