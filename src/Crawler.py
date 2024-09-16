import sqlite3
import requests
import bs4
from urllib.parse import urljoin
import re

from src.SQLiteDB import run_sql_script


class Crawler:


    def __init__(self, dbFileName, dbMigration):
        self.db_name = dbFileName
        self.db_migration = dbMigration
        self.conn = sqlite3.connect(dbFileName)
        self.cursor = self.conn.cursor()
        self.initDB()


    def __del__(self):
        self.conn.close()

    def initDB(self):
        run_sql_script(self.db_name, self.db_migration)
    # 1. Индексирование одной страницы

    def addToIndex(self, soup, url):
        if self.isIndexed(url):
            print(f"URL {url} уже проиндексирован.")
            return
        print(f"Индексация страницы: {url}")

        # Получаем текст только с текущей страницы
        text = self.getTextOnly(soup)
        words = self.separateWords(text)

        # Сохраняем страницу в БД
        self.cursor.execute("INSERT INTO pages (url, content) VALUES (?, ?)", (url, text))
        page_id = self.cursor.lastrowid

        # Индексация слов на странице
        for word in words:
            word_id = self.getEntryId('words', 'word', word)
            self.cursor.execute("INSERT INTO page_words (page_id, word_id, frequency) VALUES (?, ?, ?)",
                                (page_id, word_id, words.count(word)))

        self.conn.commit()
    # 2. Получение текста страницы

    def getTextOnly(self, soup):
        # Извлекаем текст без HTML-тегов
        text = soup.get_text()
        return text
    # 3. Разбиение текста на слова

    def separateWords(self, text):
        # Разделяем текст на слова (игнорируем все, кроме букв и цифр)
        return re.findall(r'\w+', text.lower())
    # 4. Проиндексирован ли URL (проверка наличия URL в БД)

    def isIndexed(self, url):
        self.cursor.execute("SELECT 1 FROM pages WHERE url=?", (url,))
        return self.cursor.fetchone() is not None
    # 5. Добавление ссылки с одной страницы на другую

    def addLinkRef(self, urlFrom, urlTo, linkText):
        from_id = self.getEntryId('pages', 'url', urlFrom)
        to_id = self.getEntryId('pages', 'url', urlTo)
        self.cursor.execute("INSERT INTO links (from_page_id, to_page_id) VALUES (?, ?)", (from_id, to_id))
        self.conn.commit()
    # 6. Метод сбора данных.

    def crawl(self, urlList, maxDepth=1):
        for currDepth in range(maxDepth):
            new_urls = set()  # Список новых URL для следующей глубины
            for url in urlList:
                print(f"Обход страницы: {url}")
                try:
                    html_doc = requests.get(url).text
                    soup = bs4.BeautifulSoup(html_doc, "html.parser")

                    # Индексация текущей страницы
                    self.addToIndex(soup, url)

                    # Обработка всех ссылок <a> на странице
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        full_url = urljoin(url, href.split('#')[0])  # Убираем якоря и получаем полный URL
                        if full_url not in new_urls and full_url not in urlList:
                            new_urls.add(full_url)
                            self.addLinkRef(url, full_url, link.get_text())

                except requests.RequestException as e:
                    print(f"Ошибка при загрузке страницы {url}: {e}")
            urlList = new_urls

    # 8. Вспомогательная функция для получения идентификатора и добавления записи, если такой еще нет
    def getEntryId(self, tableName, fieldName, value):
        self.cursor.execute(f"SELECT id FROM {tableName} WHERE {fieldName}=?", (value,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        self.cursor.execute(f"INSERT INTO {tableName} ({fieldName}) VALUES (?)", (value,))
        return self.cursor.lastrowid