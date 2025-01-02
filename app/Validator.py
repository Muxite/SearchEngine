import threading
import time
from queue import Empty


class Validator:
    def __init__(self, name, lock, flags, seen_links_set, in_queue, out_queue, timeout=2, batch_size=100):
        self.name = name
        self.seen_links_set = seen_links_set
        self.toggle_lock = lock
        self.flags = flags
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.timeout = timeout
        self.batch_size = batch_size
        self.thread = None
        self.operating = False


    def report(self, text):
        """
        Logs a message with the validator's name for identification purposes.

        :param text: The message to be logged or reported.
        """
        print(f"Validator {self.name}: {text}")

    def run_loop(self, check_period):
        """
        Primary loop of validator operation. Gets batches from in queue, validates batch, pushes valid to out queue.

        :param check_period: How many loops until check for operating signal.
        """
        loops = 0
        while not self.operating:
            if loops % check_period == 0:
                with self.toggle_lock:
                    self.operating = self.flags[self.name]["operating"]

            if self.operating:
                try:
                    batch = []
                    for _ in range(self.batch_size):
                        batch.append(self.in_queue.get(timeout=self.timeout))
                    if batch:
                        for item in batch:
                            if item in self.seen_links_set:
                                self.out_queue.put(item)
                except Empty:
                    time.sleep(self.timeout)

            loops += 1
