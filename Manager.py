import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
from Indexer import Indexer
from queue import Queue, Empty
from bs4 import BeautifulSoup
import pickle
from TagIndex import TagIndex


def to_decimals(val, decimals):
    """
    Round to a number of decimal places.
    :param val: Initial value.
    :param decimals: Number of decimals to round to.
    :return: Rounded result.
    """
    return round(val * 10**decimals)/10**decimals


class ScraperManager:
    def __init__(self, state_path, tag_index_path):
        self.link_queue = Queue()
        self.tag_index = TagIndex()
        self.tag_index_path = tag_index_path
        self.indexer = Indexer()
        self.state_path = state_path
        self.lock = threading.Lock()
        self.processed_links = {}
        self.scrapers = []
        self.start_flag = threading.Event()
        self.shutdown_flag = threading.Event()
        self.stop_sentinel = "stop"
        self.initial_time = 0
        self.final_time = 1
        self.opened_links = 0

    def save_tag_index(self):
        """
        Save the TagIndex to file.
        """
        self.tag_index.save_index(self.tag_index_path)
        print(f"*** Saved tag index to {self.tag_index_path}***")

    def load_tag_index(self):
        """
        Load the TagIndex from file.
        """
        self.tag_index.load_index(self.tag_index_path)
        print(f"*** Loaded tag index from {self.tag_index_path}***")

    def save_state(self):
        """
        Save the current state of the scraper to a file.
        :param path: save location
        """
        path = self.state_path
        state = {
            'link_queue' : list(self.link_queue.queue),
            'processed_links' : self.processed_links,
            'indexer' : self.indexer.serialize()
        }

        with open(path, 'wb') as file:
            pickle.dump(state, file)
        print(f"*** Saved state to {path}***")

    def load_state(self):
        """
        Load a saved scraper state from a file.
        :param path: load location
        """
        path = self.state_path
        try:
            with open(path, 'rb') as file:
                state = pickle.load(file)

            # Restore the state variables

            self.link_queue = Queue()
            for link in state['link_queue']:
                self.link_queue.put(link)

            self.processed_links = state['processed_links']  # Restore the processed links
            self.indexer.deserialize(state['indexer'])  # Restore the Indexer object
            print(f"*** State loaded from {path}***")

        except FileNotFoundError:
            print(f"No saved state file found at {path}")

    def push_data(self, current_link, found_links, text):
        """
        Safely update link queue, processed links, and tags.

        Uses a lock to push only unique links to the link queue,
        updates processed_links based on recurrences.
        :param current_link: The link the browser is on
        :param found_links: List of links
        :param text: The page's text
        """
        with self.lock:
            # Update link lists
            self.opened_links += 1
            for link in found_links:
                if link not in self.processed_links:
                    self.link_queue.put(link)
                    self.processed_links[link] = 1
                else:
                    self.processed_links[link] += 1

            # Update tags
            if text:
                tags = self.indexer.tag(text)
                self.tag_index.add_tagged_link(tags, current_link)

    def setup_browser(self):
        """
        Configure the browser for scraping.
        """
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
        return browser

    def extract_links(self, browser):
        """Extract links from the page using BeautifulSoup and Selenium."""
        a_tags = browser.find_elements(By.TAG_NAME, 'a')
        return [a.get_attribute('href') for a in a_tags]

    def extract_text(self, browser):
        """Extract text from the page source using BeautifulSoup."""
        return BeautifulSoup(browser.page_source, 'html.parser').get_text(separator=" ", strip=True)

    def process_page(self, link, browser):
        """Open the page, extract text and links, and push data."""
        browser.get(link)
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        text = self.extract_text(browser)
        found_links = self.extract_links(browser)
        self.push_data(link, found_links, text)

    def scraper(self):
        """
        A scraper agent thread.

        Opens a link in queue, process page for data and more links.
        """
        self.start_flag.wait()
        browser = self.setup_browser()

        # Maintain loop until shutdown.
        retries = 0
        while True:
            self.rates()
            try:
                link = self.link_queue.get(timeout=1)
                if link == self.stop_sentinel:
                    break
                self.process_page(link, browser)

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
        """
        # Give each scraper a stop message
        for i in self.scrapers:
            self.link_queue.put(self.stop_sentinel)

        # Wait for each thread to finish
        for scraper in self.scrapers:
            scraper.join()

        self.save_tag_index()

    def force_shutdown(self, save=False):
        """
        Immediately stop all threads and save the state.
        Ensures no further links are processed after being called.
        """

        # Save the state and tag index
        if save:
            self.save_state()
            self.save_tag_index()

        # Set the shutdown flag
        self.shutdown_flag.set()

        # Lock to safely clear and refill the queue
        with self.lock:
            # Clear the queue to discard any remaining links
            while not self.link_queue.empty():
                self.link_queue.get()

            # Send stop sentinels to halt threads
            for _ in self.scrapers:
                self.link_queue.put(self.stop_sentinel)

        # Wait for all threads to finish
        for scraper in self.scrapers:
            scraper.join()

        print("*** Forced Shutdown Complete***")

    def rates(self):
        """
        Print diagnostic info on the current performance of the scrapers.
        """
        elapsed_time = time.time() - self.initial_time

        link_gather_rate = to_decimals(len(self.processed_links) / elapsed_time, 2)
        link_view_rate = to_decimals(self.opened_links / elapsed_time, 2)
        if self.shutdown_flag.is_set():
            print(f"Viewing {link_view_rate} links/s.")
        else:
            print(f"Gathering {link_gather_rate} links/s, Viewing {link_view_rate} links/s.")

def main():
    # Initialize ScraperManager
    s = ScraperManager(r"state.pickle", r"tagIndex.pickle")

    # Load previous state and tag index
    num_scrapers = 8
    s.push_data(None, ["https://en.wikipedia.org/wiki/Main_Page"], None)
    s.start_scrapers(num_scrapers)
    shutdown_timer = threading.Timer(300, s.force_shutdown)
    shutdown_timer.start()
    s.shutdown_flag.wait()
    s.force_shutdown(save=True)
    s.save_state()
    s.save_tag_index()
    print(s.tag_index.summary())

if __name__ == "__main__":
    main()
