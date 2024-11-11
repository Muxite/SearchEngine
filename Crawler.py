import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import networkx as nx
import time
import matplotlib.pyplot as plt
# idea is to create many crawler objects each running as their own process
# each crawler will map a website
# for now, crawlers will not interact with each other


class Crawler:
    def __init__(self, name, arguments_string):
        self.name = name
        self.options = uc.ChromeOptions()
        self.state = "initializing"  # the crawler's state can be requested
        self.declare_state()
        self.browser = None
        self.already_visited = {}  # dict of links already visited
        self.node_count = 0
        self.stamina = 1
        arguments = arguments_string.split()
        for arg in arguments:
            self.options.add_argument(arg)
        self.browser = uc.Chrome(options=self.options)
        self.actions = ActionChains(self.browser)
        # browser ready
        self.state = "ready"
        self.declare_state()

        # set up crawler storage solution
        self.graph = nx.Graph()

    def declare_state(self):
        print(f"{self.name} {self.state}")


    # load browser, get to starting point
    def swing(self, starting_url, stamina=1):
        self.node_count += 1
        self.stamina = stamina
        self.browser.get(starting_url)
        self.search(starting_url)

    def wait_for_page_load(self):
        wdw(self.browser, 10).until(
            ec.presence_of_element_located((By.XPATH, "/html/body"))
        )

    def back(self):
        # browser.back()
        self.browser.execute_script("window.history.go(-1)")

    def click_link(self, link):
        wdw(self.browser, 10).until(
            ec.visibility_of(link)
        )
        if link.is_displayed() and link.size['width'] > 0 and link.size['height'] > 0:
            try:
                self.actions.click(link).perform()
                return True
            except:
                # try it again lol
                self.actions.click(link).perform()
                return True
        else:
            return False

    # when it arrives at a new page, do this
    # IMPORTANT: href != url
    def search(self, old_node_id):
        self.wait_for_page_load()
        # current_node_id = self.already_visited.get(current, self.node_count)
        # self.graph.add_node(current_node_id, content=self.browser.find_element(By.XPATH, "/html/body").text)

        if self.node_count > self.stamina:
            return

        links = self.browser.find_elements(By.XPATH, '//a')
        print(links)
        for link in links:
            # go to the site, and check the url
            href = link.get_attribute('href')
            if href:
                if self.click_link(link):
                    print(link)
                    # find the url
                    url = self.browser.current_url
                    current_node_id = self.already_visited.get(url, self.node_count)
                    # if not already visited, make a node
                    if current_node_id == self.node_count:
                        self.graph.add_node(current_node_id)
                        self.graph.add_edge(old_node_id, current_node_id)
                        self.already_visited[url] = current_node_id
                        self.node_count += 1
                        self.search(current_node_id)
                    else:
                        # make a connection and back out
                        self.graph.add_edge(old_node_id, current_node_id)
                        self.back()
                else:
                    print("link failure")
            else:
                self.graph.add_edge(current_node_id, self.already_visited[href])

    def display(self):
        nx.draw(self.graph, with_labels=True)
        plt.show()


def main():
    c = Crawler("Ape", "")
    c.swing("https://en.wikipedia.org/wiki/Main_Page", stamina=20)
    c.display()


main()
