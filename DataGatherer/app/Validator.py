import hashlib
import json
import time
import redis
from queue import Queue, Empty
import threading


def hash_text(text):
    """
    Hash the text to allow simpler duplicate detection and avoid saving the whole text.
    :param text: text to hash
    :return: hashed text
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Validator:
    def __init__(self, redis_client, queue, sync_period=1):
        """
        Initializes Syncer agent.

        :param redis_client: redis_client client instance.
        :param queue: Queue to take data out of.
        :param sync_period: Time to wait between syncs.
        """
        self.redis_client = redis_client
        self.queue = queue
        self.sync_period = sync_period
        self.running = False
        self.thread = None

    def sync(self):
        while self.running:
            try:
                link = self.queue.get(self.sync_period)
            except Empty:
                continue

            if not link:
                continue

            try:
                if link.strip() and not self.redis_client.sismember("seen_links:set", json.dumps(link)):
                    self.redis_client.sadd("seen_links:set", json.dumps(link))
                    self.redis_client.rpush("target_links:list", json.dumps(link))

            except Exception as e:
                print("Error processing:", e)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.sync, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()