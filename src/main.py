import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://history.eco/category/earth/']  # Стартовые страницы
    crawler = Crawler_module.Crawler('test3.db')
    crawler.crawl(start_pages, depth=3)  # Глубина обхода — 2
