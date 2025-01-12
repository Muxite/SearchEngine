from ValidatorManager import ValidatorManager
from ScraperManager import ScraperManager
from queue import Queue
import time
import pickle

class DataGatherer:
    def __init__(self,
                 seed,
                 out_queue,
                 autostart=True,
                 autostop=True,
                 timeout=120,
                 scrapers=8,
                 validators=1,
                 quit_timeout=2,
                 scraper_timeout=2,
                 validator_timeout=2
                 ):
        """
        An object that produces new link+text pairs from a starting seed. Takes time to start and stop.
        """
        self.out_queue = out_queue
        self.autostart = autostart
        self.autostop = autostop
        self.timeout = timeout
        self.running = False
        self.link_queue = Queue()
        self.validation_queue = Queue()
        self.Scraper = ScraperManager(seed,
                                      self.link_queue,
                                      self.validation_queue,
                                      scraper_timeout,
        )
        self.Validator = ValidatorManager(self.link_queue,
                                          self.validation_queue,
                                          timeout,
                                          validator_timeout)
        self.scrapers = scrapers
        self.validators = validators
        self.quit_timeout = quit_timeout

        if self.autostart:
            self.update_threads(self.scrapers, self.validators)
            self.start()

    def update_threads(self, scrapers, validators):
        """
        Prep threads, close some threads etc.
        :param scrapers: How many scrapers
        :param validators: How many validators
        """
        self.Scraper.update_num(self.scrapers)
        self.Validator.update_num(self.validators)
        self.scrapers = scrapers
        self.validators = validators

    def start(self):
        """
        Begin gathering links if not already running.

        :return:
        """
        if self.running:
            return

        self.running = True
        self.Scraper.send_order_all("quit", False)
        self.Scraper.send_order_all("standby", True)
        self.Scraper.send_order_all("operating", True)
        self.Validator.send_order_all("quit", True)
        self.Validator.send_order_all("operating", True)

    def quit(self):
        """
        Safely exit the program with the ability to save all data.
        Clears the "limbo" queue, and puts all links in the link queue.
        """
        self.running = False
        self.Scraper.update_num(0)
        self.scrapers = 0

        # Create a special validator to clear all remnants in validation queue.
        self.Validator.start_validator("CLEARER", 1)

        # Wait until Validator queue is clear.
        while not self.validation_queue.empty():
            time.sleep(self.quit_timeout)

        # End validators.
        self.Validator.update_num(0)
        self.validators = 0

    def save(self, location='links.pkl'):
        with open(location, 'wb') as f:
            pickle.dump(self.link_queue, f)
