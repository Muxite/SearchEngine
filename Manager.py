import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import threading
from queue import Queue, Empty
import os


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
        self.start_flag = threading.Event()
        self.shutdown_flag = threading.Event()
        self.stop_sentinel = "stop"
        self.limiter = 1000
        self.initial_time = 0
        self.final_time = 1


    def push_links(self, links):
        """
        Safely update link queue and processed links with a list of links. Shut down if limiter exceeded.

        Uses a lock to push only unique links to the link queue,
        updates processed_links based on recurrences.
        :param links: List of links
        """
        with self.lock:
            for link in links:
                if link not in self.processed_links:
                    self.link_queue.put(link)
                    self.processed_links[link] = 1
                else:
                    self.processed_links[link] += 1

                if self.link_queue.qsize() > self.limiter:
                    print("SHUTTING DOWN")
                    self.shutdown_flag.set()


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
                time.sleep(0.5)

                # Add more links if shutdown is not imminent.
                if not self.shutdown_flag.is_set():
                    a_tags = browser.find_elements(By.TAG_NAME, 'a')
                    found_links = [a.get_attribute('href') for a in a_tags]
                    self.push_links(found_links)
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
        print(f"Gathering {link_gather_rate}Hz, Viewing {link_view_rate}Hz.")

def main():
    s = ScraperManager()
    starting_link = "https://en.wikipedia.org/wiki/Main_Page"
    s.limiter = 1000
    s.push_links([starting_link])
    s.start_scrapers(6)
    s.shutdown_flag.wait()
    s.shutdown()
    print(f"Viewed {len(s.opened_links)} links")

if __name__ == "__main__":
    main()
