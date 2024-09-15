import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def parse(url):
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

        return unique_links, len(unique_links)

    except Exception as e:
        print(f"Ошибка: {e}")
        print(f"Не могу открыть {url}")
