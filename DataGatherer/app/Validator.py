import hashlib
import json
import time
import redis
from queue import Queue
import threading


def hash_text(text):
    """
    Hash the text to allow simpler duplicate detection and avoid saving the whole text.
    :param text: text to hash
    :return: hashed text
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Validator:
    def __init__(self, redis, queue, interval=1):
        self.redis = redis
        self.queue = queue
        self.interval = interval
        self.running = False
        self.thread = None

    def sync(self):
        while self.running:
            link = self.queue.get_nowait()
            if not link:
                time.sleep(self.interval)
                continue

            try:
                if not self.redis.sismember("seen_links", link):
                    self.redis.sadd("seen_links:set", link)
                    self.redis.rpush("verified_links:list", link)

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