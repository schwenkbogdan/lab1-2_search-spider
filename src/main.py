import Crawler_module

if __name__ == '__main__':
    start_pages = ['http://192.168.0.3'
                   ]  # Стартовые страницы, 'http://chipichipichapachapa.ru/''https://habr.com', 'https://history.eco'
    crawler = Crawler_module.Crawler('config.ini')
    crawler.crawl(start_pages, 2)  # Глубина обхода