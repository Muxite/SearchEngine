import json
import time
import queue
import redis
import threading


class Syncer:
    def __init__(self, redis_client, push_map=None, pull_map=None, sync_period=5):
        """
        Initializes Syncer agent.

        :param redis_client: Redis client instance.
        :param push_map: Pairings of queues to push to Redis.
        :param pull_map: Pairings of Redis to pull to queues.
        :param sync_period: Time to wait between syncs.
        """
        self.redis_client = redis_client
        self.push_map = push_map
        self.pull_map = pull_map
        self.sync_period = sync_period
        self.running = False
        self.thread = None

    def sync(self):
        """
        Continuously syncs data between queues and Redis.
        """
        while self.running:

            # push data to Redis until cannot pull more.
            for q, redis_key in self.push_map.items():
                while True:
                    try:
                        data = q.get_nowait()
                        self.redis_client.rpush(redis_key, json.dumps(data))
                    except queue.Empty:
                        break

            # Pull data from Redis until cannot pull more.
            for q, redis_key in self.pull_map.items():
                while True:
                    try:
                        data = self.redis_client.lpop(redis_key)
                        if data:
                            q.put(json.loads(data))
                    except redis.exceptions.RedisError:
                        break

            time.sleep(self.sync_period)

    def start(self):
        """
        Starts syncing using a thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.sync, daemon=True)
            self.thread.start()
            print("Syncer started.")

    def stop(self):
        """
        Stops the sync process.
        """
        self.running = False
        if self.thread:
            self.thread.join()
            print("Syncer stopped.")