from collections import Counter
from math import log

from wheel.cli import tags_f


# Convert everything to lowercase.
# Eliminate all super-common, low meaning words.
# Find term frequency.
# Use inverse document frequency and multiply TF and IDF to find most important words.

# At the same time, train Inverse Document Frequency

class Indexer:
    def __init__(self):
        self.method = "TF-IDF"
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
            "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"
        ]

    def tfidf_score(self, text, is_document=True):
        """
        Use Term Frequency X Inverse Document Frequency to score words in a text.
        :param text: Text to score.
        :param is_document: If the text counts towards the total weightings.
        :return: Scoring dictionary.
        """
        # find term frequency
        text.lower()
        words_list = text.split()
        self.sand(words_list)

        counts = Counter(words_list)
        if is_document:
            for term, value in counts.items():
                self.document_count += 1
                self.total_counts[term] = self.total_counts.get(term, 0) + value

        # Calculate scores per word in place.
        scores = {
            word: (count / len(words_list)) * (log(self.document_count / (1 + self.total_counts[word])))
            for word, count in counts.items()
        }

        return scores

    def sand(self, words_list):
        """
        Remove the most common words from a wordlist
        :param words_list: List to operate on.
        """
        for word in self.common_words:
            words_list.remove(word)

    def tag(self, text, count=4):
        """
        Returns ideal tags for indexing a given text.
        :param text: Text to index
        :param count: How many labels to make
        :return: list of strings
        """
        scores = self.tfidf_score(text)
        top_n = sorted(scores.items(), key = lambda item: item[1], reverse=True)[:count]
        return top_n
