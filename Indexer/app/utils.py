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