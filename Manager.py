import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
from Indexer import Indexer
from queue import Queue, Empty
from bs4 import BeautifulSoup


def to_decimals(val, decimals):
    """
    Round to a number of decimal places.
    :param val: Initial value.
    :param decimals: Number of decimals to round to.
    :return: Rounded result.
    """
    return round(val * 10**decimals)/10**decimals


class ScraperManager:
    def __init__(self):
        self.link_queue = Queue()
        self.lock = threading.Lock()
        self.processed_links = {}
        self.opened_links = []
        self.scrapers = []
        self.tags = []
        self.indexer = Indexer()
        self.start_flag = threading.Event()
        self.shutdown_flag = threading.Event()
        self.stop_sentinel = "stop"
        self.limiter = 1000
        self.initial_time = 0
        self.final_time = 1


    def push_data(self, links, text):
        """
        Safely update link queue, processed links, and tags.

        Uses a lock to push only unique links to the link queue,
        updates processed_links based on recurrences.
        :param links: List of links
        :param text: The page's text
        """
        with self.lock:
            # Update link lists
            for link in links:
                if link not in self.processed_links:
                    self.link_queue.put(link)
                    self.processed_links[link] = 1
                else:
                    self.processed_links[link] += 1

                if not self.shutdown_flag.is_set() and self.link_queue.qsize() > self.limiter:
                    print("SHUTTING DOWN")
                    self.shutdown_flag.set()

            # Update tags
            if text:
                tags = self.indexer.tag(text)
                self.tags.append(tags)


    def scraper(self):
        """
        A scraper agent thread.

        Opens a link in the queue, and adds found links to the queue.
        """
        self.start_flag.wait()

        # Create browser object with minimal processing settings
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--window-size=800,600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        browser = uc.Chrome(
            options=options,
            no_sandbox=False,
            user_multi_procs=True,
            use_subprocess=False
        )

        retries = 0
        while True:
            self.rates()
            try:
                link = self.link_queue.get(timeout=1)
                if link == self.stop_sentinel:
                    break
                browser.get(link)
                self.opened_links.append(link)
                WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                text = BeautifulSoup(browser.page_source, 'html.parser').get_text(separator=" ", strip=True)

                # Add more links if shutdown is not imminent.
                found_links = []
                if not self.shutdown_flag.is_set():
                    a_tags = browser.find_elements(By.TAG_NAME, 'a')
                    found_links = [a.get_attribute('href') for a in a_tags]

                # Safely push all data using a lock.
                self.push_data(found_links, text)
            except Empty:
                if retries < 1:
                    time.sleep(2)
                else:
                    break
        print("quitting")
        browser.quit()

    def start_scrapers(self, num_scrapers):
        """
        Initializes a number of scrapers.
        :param num_scrapers: The number of browsers to create.
        """
        for _ in range(num_scrapers):
            t = threading.Thread(target=self.scraper)
            self.scrapers.append(t)
            t.start()
        self.start_flag.set()  # Set the event to start all scrapers
        self.initial_time = time.time()

    def shutdown(self):
        """
        Gracefully shutdown the system.

        All links appended after this method will not be processed in this run.
        """
        # Give each scraper a stop message
        for i in self.scrapers:
            self.link_queue.put(self.stop_sentinel)

        # Wait for each thread to finish
        for scraper in self.scrapers:
            scraper.join()

    def rates(self):
        elapsed_time = time.time() - self.initial_time

        link_gather_rate = to_decimals(len(self.processed_links) / elapsed_time, 2)
        link_view_rate = to_decimals(len(self.opened_links) / elapsed_time, 2)
        if self.shutdown_flag.is_set():
            print(f"Viewing {link_view_rate} links/s.")
        else:
            print(f"Gathering {link_gather_rate} links/s, Viewing {link_view_rate} links/s.")

def main():
    s = ScraperManager()
    starting_link = "https://en.wikipedia.org/wiki/Main_Page"
    s.limiter = 256
    s.push_data([starting_link], None)
    s.start_scrapers(8)
    s.shutdown_flag.wait()
    s.shutdown()
    print(f"Viewed {len(s.opened_links)} links")
    print(s.tags)

if __name__ == "__main__":
    main()
