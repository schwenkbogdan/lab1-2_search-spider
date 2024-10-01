import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://habr.com'
                   ]  # Стартовые страницы, 'https://history.eco''https://habr.com'
    crawler = Crawler_module.Crawler('test3.db', 'config.ini')
    crawler.crawl(start_pages, 1)  # Глубина обхода
