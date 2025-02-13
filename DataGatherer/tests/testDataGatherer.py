from queue import Queue
import time

from DataGatherer.app.DataGatherer import DataGatherer


def test_data_gatherer():
    print("***STARTING DATA GATHERER TEST***")
    out_queue = Queue()
    seed = "https://pypi.org/project/pip/"

    # THE CLASS DOES THINGS
    manager = DataGatherer(seed,
                           out_queue,
                           autostart=True,
                           autostop=True,
                           timeout=120,
                           scrapers=4
                           )
    time.sleep(140)
    print(f"Scrapers surveyed {len(list(out_queue.queue))} pages")
    print("***END DATA GATHERER TEST***")


test_data_gatherer()
