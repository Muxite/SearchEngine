from Scraper import Scraper
import threading
from namegen import namegen
from queue import Queue


class ScraperManager:
    def __init__(self, link_queue, texts_queue, validate_queue, scraper_timeout=2):
        """
        Initialize the ScraperManager that handles gathering links and text.

        :param link_queue: Queue of links from the validator. Must be seeded with at least 1 valid link.
        :param texts_queue: Output queue of text that feeds the indexer.
        :param validate_queue: Output queue of links that feeds back to the validator.
        :param scraper_timeout: Delay value inside the scrapers.
        """
        self.scrapers = {}
        self.scrapers_count = 0
        self.lock = threading.Lock()
        self.flags = {}
        self.link_queue = link_queue
        self.texts_queue = texts_queue
        self.validate_queue = validate_queue
        self.scraper_timeout = scraper_timeout

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
                    "quit": False
                }
        self.scrapers_count += 1

    def update_num(self, count):
        """
        Obtain the desired number of scrapers by starting new ones or quitting existing ones.

        :param count: The desired number of scrapers
        """

        if count > self.scrapers_count:
            for _ in range(count - self.scrapers_count):
                self.start_scraper(namegen())
        elif count < self.scrapers_count:
            self.end_scrapers(self.scrapers_count - count)

    def end_scraper(self, name):
        with self.lock:
            self.flags[name]["quit"] = True
        self.scrapers_count -= 1

    def end_scrapers(self, count):
        to_end = max(count, self.scrapers_count)
        ended = 0
        for scraper in self.flags:
            if not self.flags[scraper]["quit"]:
                self.end_scraper(scraper)
                ended += 1
                if ended == to_end:
                    break