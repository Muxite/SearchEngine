from ScraperManager import ScraperManager
from queue import Queue
import time
from utils import delayed_action
import redis
from shared.utils.Syncer import Syncer
from Validator import Validator
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Run the DataGatherer to get links and text.')
    parser.add_argument("--seed", type=str, required=True, help="Starting link.")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds.")
    parser.add_argument("--scrapers", type=int, default=2, help="Number of scrapers.")
    parser.add_argument("--redis_host", type=str, default="none", help="Redis host.")
    parser.add_argument("--redis_port", type=int, default=6379, help="Redis port.")
    return parser.parse_args()

class DataGatherer:
    def __init__(self,
                 seed,
                 timeout=60,
                 scrapers=8,
                 scraper_timeout=2,
                 ):
        """
        Starts an object that takes a seed link and generates links and text to a queue.

        :param seed: Initial link.
        :param timeout: how long the code runs until shutdown.
        :param scrapers: how many browsers to use.
        :param scraper_timeout: how frequently the scrapers check for links.
        """

        self.syncer = None
        self.validator = None
        self.out_queue = Queue()
        self.timeout = timeout
        self.running = False
        self.target_link_queue = Queue()
        self.target_link_queue.put(seed)
        self.potential_link_queue = Queue()
        self.Scraper = ScraperManager(self.target_link_queue,
                                      self.out_queue,
                                      self.potential_link_queue,
                                      scraper_timeout,
        )
        self.scrapers = scrapers
        self.update_threads(self.scrapers)
        self.start()

    def connect_redis(self, host, port, sync_period):
        """
        Start agent that syncs to redis.
        Queue of potential links is converted to target links in Redis, then synced.
        """

        redis_client = redis.Redis(host=host, port=port, db=0)
        self.syncer = Syncer(
            redis_client,
            push_map=[(self.out_queue, "link_text", False, -1, "queue")],
            pull_map=[(self.target_link_queue, "target_links", False, -1)],
            sync_period=sync_period
        )
        self.syncer.start()

        self.validator = Validator(
            redis_client,
            self.potential_link_queue,
            sync_period=sync_period
        )
        self.validator.start()

    def update_threads(self, scrapers):
        """
        Prep threads, close some threads etc.
        :param scrapers: How many scrapers
        """
        self.Scraper.update_num(self.scrapers)
        self.scrapers = scrapers

    def start(self):
        """
        Begin gathering links if not already running.
        """
        if self.running:
            return

        self.running = True
        self.Scraper.send_order_all("quit", False)
        self.Scraper.send_order_all("operating", True)

        delayed_action(self.timeout, self.quit)

    def quit(self):
        """
        Safely exit the program with the ability to save all data.
        Clears the "limbo" queue, and puts all links in the link queue.
        """
        self.running = False
        self.Scraper.update_num(0)
        self.scrapers = 0

        time.sleep(10)

        if self.syncer:
            self.syncer.stop()

        if self.validator:
            self.validator.stop()

def run():
    args = parse_args()

    datagatherer = DataGatherer(
        args.seed,
        timeout=args.timeout,
        scrapers=args.scrapers,
    )

    if args.redis_host != "none":
        datagatherer.connect_redis(args.redis_host, args.redis_port, sync_period=5)


if __name__ == "__main__":
    run()