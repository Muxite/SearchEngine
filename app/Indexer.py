from collections import Counter
from math import log
import threading
import time
from queue import Empty


# Convert everything to lowercase.
# Eliminate all super-common, low meaning words.
# Find term frequency.
# Use inverse document frequency and multiply TF and IDF to find most important words.

# At the same time, train Inverse Document Frequency

class Indexer:
    def __init__(self, in_queue, out_queue, timeout=2, batch_size=10):
        """
        Take an queue of link, text pairs and put them into a link, tag pair into an out queue.
        :param in_queue: Queue of link text pairs.
        :param out_queue: Queue of link tag pairs.
        """
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.total_counts = {}
        self.document_count = 0
        self.lock = threading.Lock()
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
        self.active = True
        self.timeout = timeout
        self.batch_size = batch_size

    def tfidf_score(self, text, is_document=True):
        """
        Use Term Frequency X Inverse Document Frequency to score words in a text.
        :param text: Text to score.
        :param is_document: If the text counts towards the total weightings.
        :return: Scoring dictionary.
        """
        # find term frequency
        words_list = text.lower().split()
        self.sand(words_list, self.common_words)
        self.sand(words_list, self.punctuation)
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

    def sand(self, words_list, to_remove):
        """
        Remove the most common words from a wordlist
        :param words_list: List to operate on.
        :param to_remove: Elements to remove.
        """
        words_list[:] = [word for word in words_list if word not in to_remove]

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
            batch = []
            try:
                for _ in range(self.batch_size):
                    batch.append(self.in_queue.get(timeout=self.timeout))
                if batch:
                    for link, text in batch:
                        tags = self.tag(text)
                        self.out_queue.put((link, tags))
            except Empty:
                time.sleep(self.timeout)
