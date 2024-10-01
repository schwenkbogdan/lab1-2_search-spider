# import re
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
    def __init__(self, db_file_name, config_file):
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

    # def crawl(self, pages, depth=2):
    #     for i in range(depth):
    #         newpages = set()
    #         for page in pages:
    #             try:
    #                 c = urllib2.urlopen(page)
    #             except:
    #                 print("Не могу открыть %s" % page
    #                 continue
    #             soup = BeautifulSoup(c.read())
    #             self.addtoindex(page, soup)
    #
    #             links = soup('a')
    #
    #             for link in links:
    #                 if ('href' in dict(link.attrs)):
    #                     url = urljoin(page, link['href'])
    #                     if url.find("'") != -1: continue
    #                     url = url.split('#')[0]  # удалить часть URL после знака #
    #                     if url[0:4] == 'http' and not self.isindexed(url):
    #                         newpages.add(url)
    #                     linkText = self.gettextonly(link)
    #                     self.addlinkref(page, url, linkText)
    #             self.dbcommit()
    #
    # pages = newpages


    # 6. Непосредственно сам метод сбора данных.
    # Начиная с заданного списка страниц, выполняет поиск в ширину
    # до заданной глубины, индексируя все встречающиеся по пути страницы
    def crawl(self, url_list, depth):
        """Основной метод для обхода страниц и индексации с учётом глубины переходов"""
        self.save_urls_to_db(url_list)
        current_depth = 0
        pages_to_crawl = url_list
        crawled_urls = set()  # Для отслеживания уже обработанных URL

        while current_depth <= depth and pages_to_crawl:
            next_depth_pages = []  # Список страниц для следующей глубины
            for page in pages_to_crawl:
                if not self.is_indexed(page) and page not in crawled_urls:
                    try:
                        print(f"Получить и проанализировать страницу: {page}")
                        # Получить и проанализировать страницу
                        links = self.parse(page)
                        self.save_urls_to_db(links)
                        crawled_urls.add(page)  # Добавляем текущую страницу в обработанные

                        # Добавляем найденные ссылки только если глубина не превышена
                        if current_depth < depth:
                            next_depth_pages.extend(links)

                    except Exception as e:
                        print(f"Ошибка при обработке {page}: {e}")

            # Обновляем список страниц для следующей глубины и увеличиваем текущую глубину
            pages_to_crawl = list(set(next_depth_pages))  # Убираем дубликаты
            current_depth += 1

        print(f"Обход завершён. Всего глубина: {current_depth}, найдено уникальных URL: {len(crawled_urls)}")


    def parse(self, url):
        """Получает список адресов для поиска уникальных страниц и подсчёта их количества,
        отдаёт список найденных страниц"""
        try:
            # Получение HTML-кода страницы
            soup = self.get_soup(url)

            # Удаление ненужных элементов (script, style)
            self.remove_unwanted_tags(soup)

            # Поиск и обработка всех ссылок на странице
            unique_links = self.extract_links(soup, url)

            # Вывести список ссылок и их количество
            self.print_found_links(unique_links)

            # Обработка текста страницы и сохранение в базу данных
            self.process_page_text(soup)

            return unique_links

        except Exception as e:
            print(f"Ошибка: {e}")
            print(f"Не могу открыть {url}")


    def get_soup(self, url):
        """Получить HTML-код страницы и преобразовать его в объект BeautifulSoup"""
        html_doc = requests.get(url)
        print(f"6. crawl - Попытка открыть страницу {url}")
        soup = BeautifulSoup(html_doc.text, 'html.parser')
        return soup


    def remove_unwanted_tags(self, soup):
        """Удалить ненужные теги, такие как script и style, из объекта BeautifulSoup"""
        for tag in soup(['script', 'style']):
            tag.decompose()


    def extract_links(self, soup, base_url):
        """Найти и вернуть уникальные ссылки на том же домене, исключая игнорируемые файлы"""
        links = []
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(base_url, a_tag['href'])  # Преобразование в абсолютную ссылку

            # Проверяем, чтобы ссылка вела на тот же домен
            if urlparse(link).netloc == urlparse(base_url).netloc:
                # Игнорируем ссылки на изображения и файлы
                if not self.is_ignored_file(link):
                    links.append(link)

        # Уникализируем ссылки
        unique_links = list(set(links))
        return unique_links


    def print_found_links(self, links):
        """Вывести найденные ссылки и их количество"""
        print("\nНайденные ссылки на страницы этого сайта:")
        for link in links:
            print(link)
        print(f"\nВсего найдено ссылок: {len(links)}")


    def process_page_text(self, soup):
        """Извлечь текст, разделить его на слова и сохранить в базу данных"""
        text = self.get_text_only(soup)
        words = self.separate_words(text)
        self.save_text_to_db(words)


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
