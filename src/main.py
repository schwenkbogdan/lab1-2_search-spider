import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://history.eco'
                   ]  # Стартовые страницы, 'https://habr.com''http://www.chipichipichapachapa.ru/'
    crawler = Crawler_module.Crawler('config.ini')
    crawler.crawl(start_pages, 1)  # Глубина обхода