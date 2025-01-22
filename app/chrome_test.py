from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-images")
options.add_argument("--window-size=800,600")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
browser.get("https://en.wikipedia.org/wiki/Main_Page")
time.sleep(4)
a_tags = browser.find_elements(By.TAG_NAME, 'a')
print('hi')
print(a_tags)