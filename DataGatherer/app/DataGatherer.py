import queue

from ValidatorManager import ValidatorManager
from ScraperManager import ScraperManager
from queue import Queue
import time
import pickle
from utils import delayed_action
import redis
import json
import threading
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Run the DataGatherer to get links and text.')
    parser.add_argument("--seed", type=str, required=True, help="Starting link.")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds.")
    parser.add_argument("--scrapers", type=int, default=2, help="Number of scrapers.")
    parser.add_argument("--validators", type=int, default=1, help="Number of validators.")
    parser.add_argument("--redis_host", type=str, default="none", help="Redis host.")
    parser.add_argument("--redis_port", type=int, default=6379, help="Redis port.")
    return parser.parse_args()

class DataGatherer:
    def __init__(self,
                 seed,
                 redis_client=None,
                 autostart=True,
                 autostop=True,
                 timeout=60,
                 scrapers=8,
                 validators=1,
                 scraper_timeout=2,
                 validator_timeout=2
                 ):
        """
        Starts an object that takes a seed link and generates links and text to a queue.

        :param seed: Initial link.
        :param redis_client: redis client where data is pushed.
        :param autostart: if the code should run after initialization.
        :param autostop: if the code should shutdown after timeout.
        :param timeout: how long the code runs until shutdown.
        :param scrapers: how many browsers to use.
        :param validators: how many validators to use.
        :param scraper_timeout: how frequently the scrapers check for links.
        :param validator_timeout: how frequently the validators check for links.
        """

        self.redis_client = redis_client
        self.sync_thread = None
        self.out_queue = Queue()
        self.autostart = autostart
        self.autostop = autostop
        self.timeout = timeout
        self.running = False
        self.link_queue = Queue()
        self.link_queue.put(seed)
        self.validation_queue = Queue()
        self.Scraper = ScraperManager(self.link_queue,
                                      self.out_queue,
                                      self.link_queue,
                                      scraper_timeout,
        )
        self.Validator = ValidatorManager(self.validation_queue,
                                          self.link_queue,
                                          timeout,
                                          validator_timeout)
        self.scrapers = scrapers
        self.validators = validators

        if self.autostart:
            self.update_threads(self.scrapers, self.validators)
            self.start()

        if redis_client:
            threading.Thread(
                target=self.sync_redis,
                args=(self.redis_client,),
                daemon=True
            ).start()

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
        """
        if self.running:
            return

        self.running = True
        self.Scraper.send_order_all("quit", False)
        self.Scraper.send_order_all("operating", True)
        self.Validator.send_order_all("quit", False)
        self.Validator.send_order_all("operating", True)

        if self.autostop:
            delayed_action(self.timeout, self.quit)

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
            time.sleep(self.Validator.validator_timeout)

        # End validators.
        self.Validator.update_num(0)
        self.validators = 0
        time.sleep(5)


    def sync_redis(self, redis_client):
        """Transfers data from local queue to Redis"""
        while self.running:
            try:
                data = self.out_queue.get_nowait()
                redis_client.rpush("link_text_queue", json.dumps(data))
                print(f"Synced to Redis {data}")
            except queue.Empty:
                time.sleep(1)
            except redis.exceptions.RedisError as e:
                print(e)
                time.sleep(1)

    def save(self, location='links.pkl'):
        with open(location, 'wb') as f:
            pickle.dump(self.link_queue, f)


def run():
    args = parse_args()

    r = None
    if args.redis_host != "none":
        r = redis.Redis(host=args.redis_host, port=args.redis_port, db=0)

    datagatherer = DataGatherer(
        args.seed,
        redis_client=r,
        timeout=args.timeout,
        scrapers=args.scrapers,
        validators=args.validators
    )


if __name__ == "__main__":
    run()