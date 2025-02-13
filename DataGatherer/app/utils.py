import threading
import time

def delayed_action(timeout, action):
    """
    Threaded function that performs an action after a time passes.

    :param timeout: the amount of time to wait.
    :param action: the function to run.
    """

    def d_a():
        time.sleep(timeout)
        action()

    threading.Thread(target=d_a, daemon=True).start()


def queue_checker(queue, frequency, action):
    def worker():
        while not queue.empty():
            data = queue.get()
            action(data)
            time.sleep(1/frequency)

    threading.Thread(target=worker, daemon=True).start()

def push_list(queue, items_list):
    """
    Push a list of items to a queue.
    :param queue: destination
    :param items_list: list
    """
    for item in items_list:
        queue.put(item)