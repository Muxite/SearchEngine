import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time
import matplotlib.pyplot as plt
import multiprocessing
from queue import Empty

from tornado.gen import multi


class ScraperManager:
    def __init__(self):
        self.link_queue = multiprocessing.Queue()
        self.scrapers = []
        self.start_event = multiprocessing.Event()
        self.stop_sentinel = None

    def add_links(self, links):
        """
        Put links into the link queue.

        :param links: List of links
        :return:
        """
        for link in links:
            self.link_queue.put(link)

    def scraper(self):
        """
        A scraper agent process.

        Opens a link in the queue, and adds found links to the queue.
        """
        self.start_event.wait()
        scraper = Scraper()
        retries = 0
        # check if there is a link to work on
        while True:
            try:
                link = self.link_queue.get(timeout=1)
                if link == self.stop_sentinel:
                    break
                # Use the Scraper to get links.
            except Empty:
                # sleep incase new links come in
                if retries < 1:
                    time.sleep(30)
                else:
                    break

    def start_scraper(self):
        """
        Create a new scraper process and agent.
        """
        p  = multiprocessing.Process(target=self.scraper)
        self.scrapers.append(p)
        p.start()

    def shutdown(self):
        """
        Gracefully shutdown the system.

        All links appended after this method will not be processed in this run.
        """
        # Give each scraper a stop message
        for i in self.scrapers:
            self.link_queue.put(self.stop_sentinel)

        # Wait for each process to finish
        for scraper in self.scrapers:
            scraper.join()

class Scraper:
    def __init__(self):
        self.current_page = None
        self.options = uc.ChromeOptions()
        self.browser = uc.Chrome(options=self.options)

    def scrape(self, link):
        pass
