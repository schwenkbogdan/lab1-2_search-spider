import Crawler

# Пример использования
if __name__ == "__main__":
    # Создаем экземпляр паука и запускаем обход с начального списка URL
    crawler = Crawler.Crawler('crawler.db', 'db.sql')
    start_urls = ['https://www.gazeta.ru/']  # Замените на реальные начальные URL
    crawler.crawl(start_urls, maxDepth=2)
    del crawler  # Явно вызываем деструктор для закрытия соединения с БД