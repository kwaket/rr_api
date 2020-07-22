import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By


class TestLogin():

    @pytest.fixture
    def driver(self, request):
        driver_ = webdriver.Chrome()

        def quit():
            driver_.quit()

        request.addfinalizer(quit)
        return driver_

    def test_valid_credentials(self, driver):
        driver.get("https://rosreestr.ru")
        assert 'Росреестр' == driver.title
