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
        :param push_map: Pairings of queues to push to Redis. Copy only or push.
        :param pull_map: Pairings of Redis to pull to queues. Copy only or pull.
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
        Tuple format is: (queue, redis name, copy only?, item limit).
        An -1 item limit means there is no limit.
        """
        while self.running:

            # push data to Redis until cannot pull more.
            for q, redis_key, copy_only, limit in self.push_map:
                loops = 0
                while True:
                    try:
                        data = q.get_nowait()
                        if copy_only:
                            self.redis_client.rpush(redis_key, json.dumps(data))
                            q.put(data)
                        else:
                            self.redis_client.rpush(redis_key, json.dumps(data))
                        loops += 1

                        if limit != -1 and loops >= limit:
                            break
                    except queue.Empty:
                        break

            # Pull data from Redis until cannot pull more.
            for q, redis_key, copy_only, limit in self.pull_map:
                loops = 0
                while True:
                    try:
                        if copy_only:
                            data = self.redis_client.lindex(redis_key, 0)
                        else:
                            data = self.redis_client.lpop(redis_key)
                        if data:
                            q.put(json.loads(data))
                            loops += 1
                        else:
                            break

                        if limit != -1 and loops >= limit:
                            break

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