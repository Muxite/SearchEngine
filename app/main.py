from DataGatherer import DataGatherer
from queue import Queue
from namegen import namegen
import random
from utils import queue_checker

def main():
    out_queue = Queue()
    seed = "https://www.w3schools.com/python/python_mysql_getstarted.asp"
    DataGatherer(seed, out_queue)
    queue_checker(out_queue, 1, print)

main()