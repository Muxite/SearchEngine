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
        self.redis = redis
        self.mysql = mysql
        self.cursor = self.mysql.cursor()

        self.set = None

    def validate(self, link, text):
        if link:
            if self.redis.sismember("visited_links", link):
                return False

        if link:


