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
        self.ready = False
        self.operating = False

    def report(self, text):
        """
        Logs a message with the scraper's name for identification purposes.

        :param text: The message to be logged or reported.
        :return: None
        """
        print(f"Validator {self.name}: {text}")

    def run_loop(self):
        """
        Primary loop of validator operation. Gets batches from in queue, validates batch, pushes valid to out queue.

        :param check_period: How many loops until check for operating signal.
        """
        loops = 0
        while True:
            with self.toggle_lock:
                self.operating = self.flags[self.name]["operating"]
                quitting = self.flags[self.name]["quit"]

            if quitting:
                self.report("Exiting")
                break

            if self.operating:
                try:
                    batch = []
                    for _ in range(self.batch_size):
                        batch.append(self.in_queue.get_nowait())
                    if batch:
                        for item in batch:
                            if not item in self.seen_links_set:
                                self.out_queue.put(item)
                except Empty:
                    time.sleep(self.timeout)
            else:
                time.sleep(self.timeout)

            loops += 1

    def start(self):
        """
        Start thread if not already started.
        """
        if self.thread is None:
            self.ready = True
            self.thread = threading.Thread(target=self.run_loop)
            self.thread.start()
