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
        self.push_map = push_map or []
        self.pull_map = pull_map or []
        self.sync_period = sync_period
        self.running = False
        self.thread = None

    def sync(self):
        """
        Continuously syncs data between queues and Redis.
        Tuple format is: (queue, redis name, copy only?, item limit, sync type).
        No sync type for pulling.
        An -1 item limit means there is no limit.
        """
        while self.running:

            # push data to Redis until cannot pull more.
            for q, redis_key, copy_only, limit, sync_type in self.push_map:
                loops = 0
                while True:
                    try:
                        data = q.get_nowait()
                        dump = json.dumps(data)
                        if sync_type != "queue":
                            if not self.redis_client.sismember(redis_key, dump):
                                self.redis_client.sadd(redis_key + ":set", dump)
                        if sync_type != "set":
                            self.redis_client.rpush(redis_key + ":list", dump)

                        if copy_only:
                            q.put(data)

                        loops += 1

                        if limit != -1 and loops >= limit:
                            break
                    except queue.Empty:
                        break

            # Pull data from Redis until cannot pull more.
            for q, redis_key, copy_only, limit in self.pull_map:
                loops = 0
                while True:
                    if limit != -1 and loops >= limit:
                        break
                    try:
                        if copy_only:
                            data = self.redis_client.lindex(redis_key + ":list", loops)
                        else:
                            data = self.redis_client.lpop(redis_key + ":list")
                        if data:
                            try:
                                q.put(json.loads(data))
                                loops += 1
                            except json.decoder.JSONDecodeError:
                                print("Syncer json decode error.")
                        else:
                            break

                    except redis.exceptions.RedisError as e:
                        print("Redis error during pull:", e)
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