import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def crawl(self, url_list, depth):
    """Основной метод для обхода страниц и индексации"""
    self.save_urls_to_db(url_list)
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

def crawl(self, urls, depth):
    try:
        # Сохранить URL в базу данных
        self.save_urls_to_db(urls)

        current_depth = 0
        pages_to_crawl = urls

        while current_depth <= depth and pages_to_crawl:
            new_pages = []
            for page in pages_to_crawl:
                if not self.is_indexed(page):
                    try:
                        # Получить и проанализировать страницу
                        links = self.parse(page)
                        self.save_urls_to_db(links)

                        # Добавить новую страницу в список для следующей глубины
                        new_pages.append(page)

                    except Exception as e:
                        print(f"Ошибка при обработке {page}: {e}")

            # Обновляем список страниц для следующей глубины
            pages_to_crawl = list(set(new_pages))  # Убираем дубликаты
            current_depth += 1

    except sqlite3.Error as e:
        print(f"Ошибка при записи URL: {e}")