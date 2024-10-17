import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import selenium
import networkx

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
        self.already_list = []  # list of links already visited

        arguments = arguments_string.split()
        for arg in arguments:
            self.options.add_argument(arg)
        self.browser = uc.Chrome(options=self.options)

        # browser ready
        self.state = "ready"
        self.declare_state()

        # set up crawler storage solution


    def declare_state(self):
        print(f"{self.name} {self.state}")


    # load browser, get to starting point
    def start(self, starting_url):
        self.browser.get(starting_url)


    def back(self):
        # browser.back()
        self.browser.execute_script("window.history.go(-1)")

    def check_link(self, target_link):
        for i, link in enumerate(self.already_list):
            if link == target_link:
                # more common links will be closer to the front
                if i > 0:
                    self.already_list.pop(i)
                    self.already_list.insert(i - 1, link)

                return True
        self.already_list.append(target_link)
        return False

    # when it arrives at a new page, do this
    def search(self):
        # save this node

        links = self.browser.find_elements(By.XPATH, '//a')
        for link in links:
            # add a new link connection

            # if link is not already traversed
            if not self.check_link(link):
                # run search on that link too
                pass