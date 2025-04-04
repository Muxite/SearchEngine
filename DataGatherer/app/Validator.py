import hashlib
import hashlib
import redis


def hash_text(text):
    """
    Hash the text to allow simpler duplicate detection and avoid saving the whole text.
    :param text: text to hash
    :return: hashed text
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Validator:
    def __init__(self, redis, mysql):
        """
        Initialize validation process that moves unseen links to a view queue.
        Cross-references with Redis and MySQL as part of DataGatherer.
        """
        self.redis = redis
        self.mysql = mysql
        self.pipeline = []
        self.cursor = self.mysql.cursor()
        self.set = None

    def validate(self, link, text):
        """
        Run pipeline on a link.
        :param link:
        :param text:
        :return:
        """
        for check in self.pipeline:
            if check(link):
                break

