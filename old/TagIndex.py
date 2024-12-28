from collections import defaultdict
import pickle


class TagIndex:
    def __init__(self):
        # Index has a tag as a key, and the value is a dict of the link and popularity.
        self.index = defaultdict(lambda: defaultdict(int))

    def add_tagged_link(self, tags, link):
        """
        Add a link and its popularity to the index to its corresponding tags.
        :param tags: tags associated with the link.
        :param link: the link itself
        """
        for tag in tags:
            self.index[tag][link] += 1

    def get_links_by_tag(self, tag):
        """
        Return links for a given tag.
        :param tag: tag to search
        :return: associated links
        """
        return self.index.get(tag)