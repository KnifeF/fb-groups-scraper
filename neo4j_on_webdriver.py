"""This script just opens Neo4J server to view DB data on browser
(using selenium WebDriver). You have to be connected to the server
before running this.

*To connect neo4j through cmd (as an administrator):
cd your\path\to\neo4j-community-3.3.4\bin
neo4j console"""
import os
from selenium import webdriver
from time import sleep
from random import randint

# -*- coding: UTF-8 -*-
__author__ = "KnifeF"
__license__ = "MIT"
__email__ = "knifef@protonmail.com"

WITHOUT_EXTENSIONS = "--disable-extensions"
# Disable JavaScript From Browser
PREFERENCES = {'profile.managed_default_content_settings.javascript': 1}
CHROME_DRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'chromedriver')

PASSWORD_PATH = r"[data-test-id='password']"
CONNECT_PATH = r"[data-test-id='connect']"
QUERY_BOX_PATH = r"[role='presentation']"
MY_PASSWORD = "my_password"


def set_chrome_driver():
    """
    set 'webdriver.Chrome' with some arguments
    (to 'webdriver.ChromeOptions')
    :return:
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(WITHOUT_EXTENSIONS)
    # chrome_options.add_experimental_option("prefs", PREFERENCES)
    chrome_driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH,
                                     chrome_options=chrome_options)
    return chrome_driver


def run_neo_server():
    """
    use 'webdriver.Chrome' to open browser on 'localhost:7474',
    and access Neo4J GDB data (enters username and password to access db)
    :return:
    """
    driver = set_chrome_driver()
    driver.get("http://localhost:7474")
    sleep(randint(5, 10))

    input_elem = driver.find_elements_by_css_selector(PASSWORD_PATH)

    if input_elem:
        input_elem[0].send_keys(MY_PASSWORD)
        sleep(2)
        btn_elem = driver.find_elements_by_css_selector(CONNECT_PATH)
        if btn_elem:
            btn_elem[0].click()

            print("done!")

            exit_loop = False
            while not exit_loop:
                to_quit = input("enter 'q' to quit")
                if 'q' == to_quit or 'quit' == to_quit:
                    exit_loop = True
            if driver:
                driver.close()


if __name__ == '__main__':
    run_neo_server()
