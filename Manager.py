import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time
import matplotlib.pyplot as plt
import multiprocessing
from queue import Empty


class ScraperManager:
    def __init__(self):
        self.link_queue = multiprocessing.Queue()
        self.lock = multiprocessing.Lock()
        self.processed_links = {}
        self.scrapers = []
        self.start_event = multiprocessing.Event()
        self.stop_sentinel = None

    def push_links(self, links):
        """
        Safely update link queue and processed links with a list of links.

        Uses a lock to push only unique links to the link queue,
        updates processed_links based on recurrences.
        :param links: List of links
        """

        # Only 1 scraper can access at a time.
        with self.lock:
            for link in links:
                if link not in self.processed_links:
                    self.link_queue.put(link)
                    self.processed_links[link] = 1
                else:
                    self.processed_links[link] += 1

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
                found_links = scraper.scrape(link)
                self.push_links(found_links)

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
        self.actions = ActionChains(self.browser)

    def scrape(self, link):
        """
        Get all links on a page of a given link.
        :param link: The link to navigate to.
        :return: A list of found links.
        """
        self.browser.get(link)
        # wait

        # get links
        a_tags = self.browser.find_elements_by_tag_name('a')
        found_links = [a_tags.get_attribute('href')]

        # gather info about the page

        return found_links
