import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://history.eco'
                   ]  # Стартовые страницы, 'https://habr.com'
    crawler = Crawler_module.Crawler('test3.db', config_file='config.ini')
    crawler.crawl(start_pages, 1)  # Глубина обхода
