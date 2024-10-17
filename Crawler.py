import undetected_chromedriver as uc
import selenium

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

    def reverse(self):
        # driver.back()
        driver.execute_script("window.history.go(-1)")