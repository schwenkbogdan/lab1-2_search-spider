import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://history.eco'
                   ]  # Стартовые страницы, 'http://90.189.211.2/''https://habr.com'
    crawler = Crawler_module.Crawler('test3.db', 'config.ini')
    crawler.crawl(start_pages, 2)  # Глубина обхода
