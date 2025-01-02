import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import threading
import time
from queue import Empty

class Scraper:
    def __init__(self, name, lock, flags, in_queue, texts_queue, validate_queue, timeout=2):
        """

        :param name: Name, also the key in flags.
        :param lock: Lock for checking flags.
        :param flags: Dict of all flags.
        :param in_queue: The queue of links.
        :param texts_queue: Output queue for text.
        :param validate_queue: Output queue of raw links.
        :param timeout: Seconds to wait
        """
        self.name = name
        self.toggle_lock = lock  # lock for scrapers
        self.flags = flags
        self.in_queue = in_queue
        self.texts_queue = texts_queue
        self.validate_queue = validate_queue
        self.timeout = timeout
        self.ready = False
        self.operating = False
        self.browser = None
        self.thread = None

    def _init_browser(self):
        """
        Start scraper browser, configure the browser.

        return: configured browser
        """

        if self.ready:
            self.report("Already Ready")
            return self.browser

        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")
        options.add_argument("--window-size=800,600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        browser = uc.Chrome(
            options=options,
            no_sandbox=False,
            user_multi_procs=True,
            use_subprocess=False
        )
        self.ready = True
        return browser

    def start(self):
        if not self.ready:
            self.ready = True
            self.thread = threading.Thread(target=self.run_loop)
            self.thread.start()

    def get_page(self, url):
        """
        Get text from a link's webpage.

        :param url: Link to try.
        :return: The text from the link
        :return: All links found on the link.
        """
        self.browser.get(url)
        WebDriverWait(self.browser, self.timeout).until(ec.presence_of_element_located((By.TAG_NAME, "body")))
        text = self.browser.find_element(By.TAG_NAME, "body").text
        a_tags = self.browser.find_elements(By.TAG_NAME, 'a')
        found_links = [a.get_attribute('href') for a in a_tags]
        return text, found_links

    def report(self, text):
        """
        Logs a message with the scraper's name for identification purposes.

        :param text: The message to be logged or reported.
        :return: None
        """
        print(f"Scraper {self.name}: {text}")

    def run_loop(self):
        """
        Primary loop of scraper operation. Pops from in queue, pushes to text queue and validation queue.

        :return: None
        """

        if not self.ready:
            self.report("Not ready")
            return None

        loops = 0
        while True:
            # periodically check for start/shutdown signal
            with self.toggle_lock:
                self.operating = self.flags[self.name]["operating"]
                flags_ready = self.flags[self.name]["ready"]
                quitting = self.flags[self.name]["quit"]

            if quitting:
                # close browser, close thread
                self._shutdown()
                self._exit()
                break

            if flags_ready and not self.ready:
                self._init_browser()
            elif not flags_ready and self.ready:
                self._shutdown()

            # regular operation
            if self.ready and self.operating:
                try:
                    link = self.in_queue.get(timeout=self.timeout)
                    text, found_links = self.get_page(link)
                    self.texts_queue.put((link, text))
                    self.validate_queue.put(found_links)
                except Empty:
                    time.sleep(self.timeout)
            else:
                time.sleep(self.timeout)

            loops += 1

    def _shutdown(self):
        """
        Close the scraper session resources and save if started. Must start up again to become operational.
        :return: None
        """

        if self.browser:
            self.browser.quit()
            self.browser = None
            self.operating = False
            self.ready = False
        self.report("Shutting down.")

    def _exit(self):
        """
        Close the thread.
        :return:
        """
        if self.thread is not None:
            self.thread.join()
            self.thread = None
        self.report("Exiting.")