from ScraperManager import ScraperManager
from queue import Queue
import time

def test_scraper_manager():
    print("***STARTING SCRAPER MANAGER TEST***")
    link_queue = Queue()
    texts_queue = Queue()
    validate_queue = Queue()
    link_queue.put("https://pypi.org/project/pip/")
    link_queue.put("https://pypi.org/project/pip/")
    link_queue.put("https://pypi.org/project/pip/")
    link_queue.put("https://pypi.org/project/pip/")
    link_queue.put("https://pypi.org/project/pip/")

    manager = ScraperManager(
        link_queue=link_queue,
        texts_queue=texts_queue,
        validate_queue=validate_queue,
        scraper_timeout=2,
    )

    manager.update_num(3)
    print(manager.scrapers_count)
    manager.send_order_all("operating", True)
    time.sleep(20)
    print(list(link_queue.queue))
    print(list(texts_queue.queue))
    print(list(validate_queue.queue))
    manager.update_num(0)
    print(manager.scrapers_count)
    print("***END SCRAPER MANAGER TEST***")


test_scraper_manager()
