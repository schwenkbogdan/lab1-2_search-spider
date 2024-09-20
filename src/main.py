import Crawler_module

if __name__ == '__main__':
    start_pages = ['https://history.eco']  # Стартовые страницы
    crawler = Crawler_module.Crawler('test.db')
    crawler.crawl(start_pages, depth=2)  # Глубина обхода — 2
