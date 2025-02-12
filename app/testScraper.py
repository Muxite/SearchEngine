from Scraper import Scraper
from queue import Queue
import time
import threading
from utils import delayed_action

def test_Scraper():
    # creating queues for text and validation
    print("***START SCRAPER TEST***")
    texts_queue = Queue()
    validate_queue = Queue()
    in_queue = Queue()

    # URL to scraper
    url = "https://pypi.org/project/pip/"
    in_queue.put(url)
    url = "https://en.wikipedia.org/wiki/Main_Page"
    in_queue.put(url)
    # creating flags for Scraper
    flags = {"0000": {"operating": True, "quit": False}}

    lock = threading.Lock()
    scraper = Scraper("0000", lock, flags, in_queue, texts_queue, validate_queue)
    scraper.start()
    time.sleep(4)
    time.sleep(10)

    print(list(in_queue.queue))
    print(list(texts_queue.queue))
    print(list(validate_queue.queue))
    flags["0000"]["quit"] = True
    print("***END SCRAPER TEST***")

if __name__ == '__main__':
    test_Scraper()