import os

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

from settings import SAVED_RESPONSES

class TestSelenium():

    @pytest.fixture
    def driver(self, request):
        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": SAVED_RESPONSES,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        }
        options.add_experimental_option('prefs', prefs)
        if os.getenv('RR_APPLICATIONS_API_CONFIG') == 'DEV':
            driver_ = webdriver.Chrome(options=options)
        else:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--remote-debugin-port=9222")
            options.add_argument("--screen-size=1200x800")
            driver_ = webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub',
                desired_capabilities=options.to_capabilities())

        def quit():
            driver_.quit()

        request.addfinalizer(quit)
        return driver_

    def test_valid_credentials(self, driver):
        driver.get("https://rosreestr.ru")
        assert 'Росреестр' == driver.title
