import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver import ActionChains
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
        time.sleep(1)

    def back(self):
        # browser.back()
        self.browser.execute_script("window.history.go(-1)")

    def check_link(self, target_link):
        return target_link in self.already_visited

    def click_link(self, link):
        if link.is_displayed() and link.size['width'] > 0 and link.size['height'] > 0:
            try:
                self.actions.click(link).perform()
                return True
            except Exception as error_code:
                print(f"click error: {error_code}")
        else:
            return False

    # when it arrives at a new page, do this
    def search(self, current):
        self.wait_for_page_load()
        current_node_id = self.already_visited.get(current, self.node_count)
        self.graph.add_node(current_node_id, content=self.browser.find_element(By.XPATH, "/html/body").text)

        if self.node_count > self.stamina:
            return

        links = self.browser.find_elements(By.XPATH, '//a')
        for link in links:
            new = link.get_attribute('href')
            if new and not self.check_link(new):
                if self.click_link(link):
                    new_node_id = self.node_count
                    self.already_visited[new] = self.node_count
                    self.graph.add_node(new_node_id)
                    self.graph.add_edge(current_node_id, new_node_id)
                    self.node_count += 1
                    self.search(new)
                else:
                    print("link failure")
            else:
                if new:
                    self.graph.add_edge(current_node_id, self.already_visited[new])

    def display(self):
        nx.draw(self.graph, with_labels=True)
        plt.show()


def main():
    c = Crawler("Ape", "")
    c.swing("https://muxite.github.io/", stamina=20)
    c.display()


main()
