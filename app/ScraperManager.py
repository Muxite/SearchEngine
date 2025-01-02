from Scraper import Scraper
import threading
from queue import Queue


class ScraperManager:
    def __init__(self, seed, threads, link_queue, texts_queue, validate_queue, timeout, scraper_timeout=2):
        """
        Initialize the ScraperManager that handles gathering links and text.
    
        :param seed: The starting link to scrape, which will be added to the link queue.
        :param threads: Number of threads to run for managing the scrapers.
        :param link_queue: Queue of links from the validator.
        :param texts_queue: Output queue of text that feeds the indexer.
        :param validate_queue: Output queue of links that feeds back to the validator.
        :param timeout: Max time the scraper manager will run.
        :param scraper_timeout: Delay value inside the scrapers.
        """
        self.scrapers = {}
        self.lock = threading.Lock()
        self.flags = {}
        self.link_queue = link_queue
        self.texts_queue = texts_queue
        self.validate_queue = validate_queue
        self.scraper_timeout = scraper_timeout
        self.link_queue.put(seed)
        self.timeout = timeout

    def send_order_all(self, flag, value):
        """
        Flag change to all scrapers.

        :param flag: The name of the flag.
        :param value: Value to set it to.
        :return: None
        """
        with self.lock:
            for scraper in self.scrapers:
                self.flags[scraper][flag] = value

    def start_scraper(self, name):
        """
        Start a scraper instance, browser open but not operating. It will listen to its flags.

        :param name: Name of the scraper.
        :return: None
        """

        with (self.lock):
            if name not in self.scrapers:
                self.scrapers[name] = Scraper(
                    name,
                    self.lock,
                    self.flags,
                    self.link_queue,
                    self.texts_queue,
                    self.validate_queue,
                    self.scraper_timeout
                )
                self.scrapers[name].start()
                self.flags[name] = {
                    "operating": False,
                    "standby": True,
                    "quit": False
                }

