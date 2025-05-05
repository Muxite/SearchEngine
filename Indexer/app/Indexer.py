from collections import Counter
from math import log
import threading
import time
import queue
import redis
from shared.utils.Syncer import Syncer
import argparse
from utils import delayed_action


def parse_args():
    parser = argparse.ArgumentParser(description='Run the Indexer to turn text to tags.')
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds.")
    parser.add_argument("--redis_host", type=str, default="none", help="Redis host.")
    parser.add_argument("--redis_port", type=int, default=6379, help="Redis port.")
    return parser.parse_args()

# Convert everything to lowercase.
# Eliminate all super-common, low meaning words.
# Find term frequency.
# Use inverse document frequency and multiply TF and IDF to find most important words.

# At the same time, train Inverse Document Frequency

def clean(words_list, to_remove):
    for char in to_remove:
        words_list.remove(char)


def sand(words_list, to_remove):
    """
    Remove the most common words from a wordlist
    :param words_list: List to operate on.
    :param to_remove: Elements to remove.
    """
    words_list[:] = [word for word in words_list if word not in to_remove]


class Indexer:
    def __init__(self, timeout=120, worker_timeout=2):
        """
        Take a queue of link, text pairs and put them into a link, tag pair into an out queue.
        :param redis_client: redis client to sync with.
        :param in_queue: Queue of link text pairs.
        :param out_queue: Queue of link tag pairs.
        """
        self.in_queue = queue.Queue()
        self.out_queue = queue.Queue()
        self.lock = threading.Lock()
        self.total_counts = {}
        self.document_count = 0
        self.common_words = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
            "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
            "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
            "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
            "even", "new", "want", "because", "any", "these", "give", "day", "most", "us", "was", "is"
        ]
        self.punctuation = [
            '.', ',', ';', ':', '!', '?', '-', '_', '=', '+', '*', '/', '%', '(', ')', '[', ']', '{', '}',
            "'", '"', '“', '”', '‘', '’', '<', '>', '©', '®', '™', '$', '#', '@', '&', '^', '~', '|', '\\',
            '€', '£', '¥', '•', '¶', '…', '—', '›', '‹', '•', '...', '–'
        ]
        self.redis_client = None
        self.syncer = None
        self.timeout = timeout
        self.active = False
        self.worker_timeout = worker_timeout
        self.start(self.timeout)

    def connect_redis(self, host, port, sync_period):
        """
        Start agent that syncs to redis.
        Link text is pulled, and pushed as link tags.
        """
        self.syncer = Syncer(
            redis_client=self.redis_client,
            push_map=[(self.out_queue, "link_tag", False, -1, "queue")],
            pull_map=[(self.in_queue, "link_text", False, -1)],
            sync_period=sync_period
        )
        self.syncer.start()

    def start(self, timeout):
        self.active = True
        delayed_action(timeout, self.quit)
        thread = threading.Thread(
            target=self.loop
        )
        thread.start()

    def quit(self):
        self.active = False
        time.sleep(10)
        if self.syncer:
            self.syncer.stop()

    def tfidf_score(self, text, is_document=True):
        """
        Use Term Frequency X Inverse Document Frequency to score words in a text.
        :param text: Text to score.
        :param is_document: If the text counts towards the total weightings.
        :return: Scoring dictionary.
        """
        # find term frequency
        words_list = text.lower().split()
        sand(words_list, self.common_words)
        sand(words_list, self.punctuation)
        counts = Counter(words_list)
        if is_document:
            with self.lock:
                for term, value in counts.items():
                    self.document_count += 1
                    self.total_counts[term] = self.total_counts.get(term, 0) + value

        # Calculate scores per word in place.
        with self.lock:
            scores = {
                word: (count / len(words_list)) * (log(self.document_count / (1 + self.total_counts[word])))
                for word, count in counts.items()
            }

        return scores

    def tag(self, text, count=3):
        """
        Returns ideal tags for indexing a given text.
        :param text: Text to index
        :param count: How many labels to make
        :return: list of strings
        """
        if not text:
            return []

        scores = self.tfidf_score(text)
        top_n = sorted(scores.items(), key = lambda item: item[1], reverse=True)[:count]
        return [word for word, _ in top_n]

    def loop(self):
        """
        Primary loop of Indexer object. Pop link and text into a link and tag queue.
        :return:
        """
        while self.active:
            try:
                link, text = self.in_queue.get_nowait()
                tags = self.tag(text, count=5)
                self.out_queue.put((link, tags))
            except queue.Empty:
                time.sleep(self.worker_timeout)


def run():
    args = parse_args()

    indexer = Indexer(
        timeout=args.timeout,
    )

    if args.redis_host != "none":
        indexer.connect_redis(args.redis_host, args.redis_port, sync_period=5)


if __name__ == "__main__":
    run()
