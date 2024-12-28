import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from queue import Empty

class Scraper:
    def __init__(self, name, locks, flags, in_queue, texts_queue, validate_queue, timeout=2):
        self.name = name
        self.toggle_lock = locks["toggle"]
        self.flags = flags
        self.in_queue = in_queue
        self.texts_queue = texts_queue
        self.validate_queue = validate_queue
        self.timeout = timeout
        self.standby = False
        self.operating = False
        self.browser = self.start()


    def start(self):
        """
        Start scraper browser, configure the browser.

        return: configured browser
        """

        if self.standby:
            self.report("Already standby")
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
        self.standby = True
        return browser

    def get_page(self, url):
        """
        Get text from a link's webpage.

        :param url: Link to try.
        :return: The text from the link
        :return: All links found on the link.
        """
        self.browser.get(url)
        WebDriverWait(self.browser, self.timeout).until(ec.presence_of_element_located((By.TAG_NAME, "body")))
        text = BeautifulSoup(self.browser.page_source, 'html.parser').get_text(separator=" ", strip=True)
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

    def run_loop(self, check_period):
        """
        Primary loop of scraper operation. Pops from in queue, pushes to out queue.

        :param check_period: How many loops until check for operating and shutdown signals.
        :return: None
        """

        if not self.standby:
            self.report("Not standby")
            return None

        loops = 0
        while True:

            # periodically check for start/shutdown signal
            if loops % check_period == 0:
                with self.toggle_lock:
                    self.operating = self.flags[self.name]["operating"]
                    standby = self.flags[self.name]["standby"]

                    if standby and not self.standby:
                        self.start()
                    elif not standby and self.standby:
                        self.shutdown()


            if self.standby and self.operating:
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

    def shutdown(self):
        """
        Close the scraper session resources and save if started. Must start up again to become operational.
        """

        if self.standby:
            # clean up, shut down
            self.report("Shutting down.")
            self.browser.quit()
            self.standby = False
