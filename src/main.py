import Crawler_module

if __name__ == '__main__':
    start_pages = ['http://www.chipichipichapachapa.ru/'
                   ]  # Стартовые страницы, 'https://habr.com''https://history.eco'
    crawler = Crawler_module.Crawler('test3.db', 'config.ini')
    crawler.crawl(start_pages, 1)  # Глубина обхода
