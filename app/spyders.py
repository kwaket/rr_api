import os
from contextlib import suppress
import time
import logging
from datetime import datetime
import random

from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
    TimeoutException, StaleElementReferenceException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

import app.services as services

from settings import (EGRN_KEY, SAVED_CAPTCHA, SAVED_RESPONSES,
                      APPLICATION_DIR, EXCEPTION_DIR)
from app.utils.recognizer import recognize
from app.utils.file_utils import unzip_file, get_zip_content_list
from app.utils.xml_converter import get_html
from app.utils.regions.regions import Region
from app.schemas import ApplicationState
from app.db import SessionLocal


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


AUTH_ATTEMPTS = 5


def clean_key(word):
    if word.endswith(':'):
        word = word[:-1]
    return word.strip()


def get_region_rr(cadnum):
    region = Region()
    return region.get_region_rr(cadnum)


def logger(func):
    def wrapper(*args, **kwargs):
        application_id = args[0].current_application_id or 'Out of task'
        logging.info('%s: start %s. Args: %s, kwargs, %s', application_id,
                     func.__name__, str(args), str(kwargs))
        res = func(*args, **kwargs)
        logging.info('%s: end %s', application_id, func.__name__)
        return res
    return wrapper


class ExecutorError(Exception):
    pass


class EGRNBase():

    def __init__(self):
        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": SAVED_RESPONSES,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        }
        options.add_experimental_option('prefs', prefs)
        if os.getenv('RR_APPLICATIONS_API_CONFIG') == 'DEV':
            self.driver = webdriver.Chrome(options=options)
        else:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--remote-debugin-port=9222")
            options.add_argument("--screen-size=1200x800")
            self.driver = webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub',
                desired_capabilities=options.to_capabilities())
        self.current_application_id = None
        self.service_url = 'https://rosreestr.ru'
        self.service_title = 'Запрос посредством доступа к ФГИС ЕГРН'
        self.db = SessionLocal()

    def _set_application_id(self, application_id):
        self.current_application_id = application_id
        return self.current_application_id

    @logger
    def close(self):
        with suppress(WebDriverException):
            self.driver.close()
        self.db.close()

    @logger
    def _go_to_service(self):
        self.driver.get(self.service_url)
        try:
            WebDriverWait(self.driver, timeout=20).until(
                expected_conditions.title_contains(self.service_title))
        except TimeoutException:
            raise ExecutorError(
                'Не удалось загрузить страницу сервиса ' + self.service_url)


    @logger
    def _go(self, url):
        while True:
            try:
                self.driver.get(url)
            except TimeoutException:
                print("Timeout, retrying...")
                continue
            else:
                break

    @logger
    def _click_by(self, xpath):
        elem = self.driver.find_element_by_xpath(xpath)
        elem.click()

    @logger
    def _wait_element(self, xpath, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout=timeout).until(
                lambda d: d.find_element_by_xpath(xpath))
        except TimeoutException:
            return None
        else:
            return element

    @logger
    def _wait_and_click(self, xpath, timeout=10):
        elem = self._wait_element(xpath, timeout=timeout)
        elem.click()

    @logger
    def _recognize_captcha(self, captcha):
        captcha_path = self._save_captcha(captcha)
        code = recognize(captcha_path)
        if code:
            os.remove(captcha_path)
        return code

    @staticmethod
    def _take_screenshot(element, filename):
        elem = element.screenshot_as_png
        with open(filename, 'wb') as f:
            f.write(elem)
        return filename

    @logger
    def _save_captcha(self, element):
        filename = os.path.join(SAVED_CAPTCHA, element.id + '.png')
        return self._take_screenshot(element, filename)

    @staticmethod
    def _fill_field(field, value):
        for char in value:
            field.send_keys(char)
            time.sleep(random.uniform(.1, .5))

    def _save_exception_state(self, message=None):
        application_id = str(self.current_application_id) or 'out_of_task'
        now = datetime.now()
        day = now.strftime('%d.%m.%y')
        time_ = now.strftime('%H%M%S_%f')
        folder = os.path.join(EXCEPTION_DIR, application_id, day, time_)
        with suppress(FileExistsError):
            os.makedirs(folder)
        self.driver.save_screenshot(os.path.join(folder, "error.png"))
        with open(os.path.join(folder, 'error.html'), 'w') as f:
            f.write(self.driver.page_source)
        if message and isinstance(message, str):
            with open(os.path.join(folder, 'message.txt'), 'w') as f:
                f.write(message)


class EGRNApplication(EGRNBase):

    def __init__(self, egrn_key=None):
        EGRNBase.__init__(self)
        self.egrn_key = egrn_key or EGRN_KEY
        self.is_auth = False
        self.service_url = 'https://rosreestr.ru/wps/portal/p/cc_present/ir_egrn'

    @logger
    def login(self):
        self.is_auth = self._login()
        if self.is_auth:
            return True
        attempts = AUTH_ATTEMPTS
        while not self.is_auth and attempts:
            attempts -= 1
            self._save_exception_state(message='auth false')
            logging.warning('Try to loggin again. Attempts left: %s' % attempts)
            self.is_auth = self._login()
            if self.is_auth:
                return True
        raise ExecutorError(
            """Не удалось авторизоваться на сервисе росреестра. Количество попыток: %s"""
            % AUTH_ATTEMPTS)

    def _login(self):
        self._go_to_service()
        self._wait_element('.//div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input', 5)
        key_fields = self.driver.find_elements_by_xpath(
            './/div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        for field, part in zip(key_fields, self.egrn_key.split('-')):
            field.clear()
            self._fill_field(field, part)
        time.sleep(1)
        _key_fields = self.driver.find_elements_by_xpath(
            './/div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        _key = '-'.join([k.get_attribute('value') for k in _key_fields])
        if _key != self.egrn_key:
            return False

        self._wait_and_click('//span[text()="Войти"]')

        next_page_elem_xpath = '//span[text()="Поиск объектов недвижимости"]'
        self._wait_element(next_page_elem_xpath, timeout=10)
        next_page_element = self.driver.find_elements_by_xpath(
            next_page_elem_xpath)
        if not next_page_element:
            logging.info('%s: next element page not found',
                         self.current_application_id)
        return next_page_element

    @logger
    def fill_captcha(self):
        captcha_pic = self._wait_element('//img[contains(@src, "captcha")]')
        code = self._recognize_captcha(captcha_pic)
        while not code:
            time.sleep(3)
            self._wait_and_click(
                '//span[@class="v-button-caption" and text()="Другую картинку"]')
            captcha_pic = self._wait_element('//img[contains(@src, "captcha")]')
            code = self._recognize_captcha(captcha_pic)

        captcha_field = self.driver.find_element_by_xpath(
            '//div[@name="ibmMainContainer"]//input[@type="text"]')
        time.sleep(1)
        while captcha_field.get_property('value') != code:
            captcha_field.clear()
            captcha_field.send_keys(code)
            time.sleep(3)
            logging.info('%s Trying to fill captcha again',
                         self.current_application_id)

    def order_application(self, application_id):
        try:
            application = self._order_application(application_id)
        except ExecutorError as exc:
            prefix = 'Нe удалось заказать выписку'
            error_message = '{prefix}. {message}'.format(prefix=prefix,
                                                         message=str(exc))
            application = services.update_application(
                self.db, application_id,
                {'state': 'error',
                 'error_message': error_message})
        except Exception as exc:
            self._save_exception_state(str(exc))
        else:
            application.error_message = None
        return application

    @logger
    def _order_application(self, application_id):
        self._set_application_id(application_id)
        application = services.get_application(self.db, application_id)
        application.state = ApplicationState.adding
        application = services.update_application(self.db, application.id,
                                                  dict(application))
        if not self.is_auth:
            self.login()
            time.sleep(1)
            logging.info('login succes')
        else:
            self._go_to_service()

        self._wait_and_click('//span[text()="Поиск объектов недвижимости"]',
                             timeout=10)
        self._wait_element('//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input',
                           timeout=20)
        fields = self.driver.find_elements_by_xpath(
            '//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        cadnum_field, region_field = fields[0], fields[2]
        cadnum_field.send_keys(application.cadnum)
        region = get_region_rr(application.cadnum)
        region_field.send_keys(region)
        self._wait_element('//*[@id="VAADIN_COMBOBOX_OPTIONLIST"]')
        xpath = '//*[@id="VAADIN_COMBOBOX_OPTIONLIST"]//*[text()="{}"]'
        self._click_by(xpath.format(region))

        self.driver.find_element_by_xpath('//span[text()="Найти"]').click()

        self._wait_and_click(
            '//td[contains(@class, "v-table-cell-content-cadastral_num")]')

        self.fill_captcha()

        # Иногда всплывает окно "ожидание ответа".
        # Необходимо дождаться пока окно пропадет иначе программа падает
        popup = self.driver.find_elements_by_class_name('popupContent')
        popup = [e for e in popup if e.is_displayed()]
        while popup:
            popup = self.driver.find_elements_by_class_name('popupContent')
            popup = [e for e in popup if e.is_displayed()]
            time.sleep(1)

        time.sleep(3)
        self._wait_and_click('//span[text()="Отправить запрос"]')

        # Всплывающее окно
        ## Номер заявки
        result_elements = self._wait_element('//div[@class="popupContent"]//b')
        logging.info('result %s', result_elements)
        if result_elements:
            application = services.update_application(self.db, application.id,
                                                      {'foreign_id': result_elements.text,
                                                       'state': ApplicationState.added})
            logging.info('Got application id %s', application.foreign_id)
        else:
            message = self._wait_element('//div[@class="popupContent"]').text
            logging.info(message)
            application = services.update_application(self.db, application.id,
                                                      {'state': ApplicationState.error,
                                                       'message': str(message)})

            raise ExecutorError(message)

        ## Продолжить работу
        self.driver.find_element_by_xpath(
            '//span[text()="Продолжить работу"]').click()
        return application

    def _get_results(self):
        main_block = self.driver.find_element_by_class_name('v-app')
        results = main_block.find_elements_by_class_name('v-table-table')
        if not results:
            raise ValueError('Too much or too few results found')
        return results

    def update_application_state(self, application_id):
        try:
            application = self._update_application_state(application_id)
        except ExecutorError as exc:
            prefix = 'Нe удалось обновить данные по выписке'
            error_message = '{prefix}. {message}'.format(prefix=prefix,
                                                         message=str(exc))
            application = services.update_application(
                self.db, application_id,
                {'state': 'error',
                 'error_message': error_message})
        except Exception as exc:
            self._save_exception_state(str(exc))
        else:
            application.error_message = None
        return application

    @logger
    def _update_application_state(self, application_id: int):
        self._set_application_id(application_id)
        application = services.get_application(self.db, application_id)
        if not application.foreign_id:
            raise ExecutorError('Номер выписки не найден')
        application = services.update_application(
            self.db, application.id, {'state': ApplicationState.updating})
        if not self.is_auth:
            self.login()
            time.sleep(5)
        else:
            self._go_to_service()

        self._wait_and_click('//span[text()="Мои заявки"]', timeout=10)

        filter_input = self._wait_element('//*[@class="v-textfield"]')
        filter_input.send_keys(application.foreign_id)

        self._wait_and_click('//span[text() = "Обновить"]')
        time.sleep(5)

        attempt = 10
        while attempt:
            try:
                results = self._get_results()
                cells = results[0].find_elements_by_xpath('.//td')
            except StaleElementReferenceException:
                logging.warning('Getting result again...')
                self.driver.refresh()
                attempt -= 1
                time.sleep(1)
            else:
                break

        app_id, app_created, app_status = [c.text for c in cells[:3]]
        options = {
            'foreign_id': app_id,
            'foreign_created': datetime.strptime(
                app_created, '%d.%m.%Y %H:%M').isoformat(),
            'foreign_status': app_status}

        if app_status == 'Завершена':
            logging.info('downloading result')
            time.sleep(2)
            results = self._get_results()
            cells = results[0].find_elements_by_xpath('.//td')
            dwnld_btn = cells[-1].find_element_by_xpath('.//a')
            self._go(dwnld_btn.get_attribute('href'))

            while True:
                time.sleep(1)
                incompleted = os.listdir(SAVED_RESPONSES)
                incompleted = [f for f in incompleted if f.endswith('.crdownload')]
                if not incompleted:
                    break

            response_dir = os.path.join(SAVED_RESPONSES, app_id)
            filename = os.path.join(SAVED_RESPONSES,
                                    'Response-{}.zip'.format(app_id))
            response_dir = unzip_file(filename, response_dir)
            res = [f for f in os.listdir(response_dir) if f.endswith('.zip')][0]

            xml_file = get_zip_content_list(
                os.path.join(SAVED_RESPONSES, app_id, res))[0]
            unzip_file(os.path.join(SAVED_RESPONSES, app_id, res), response_dir)

            html = get_html(os.path.join(SAVED_RESPONSES, app_id, xml_file))

            with suppress(FileExistsError):
                os.makedirs(os.path.join(APPLICATION_DIR, app_id))

            result_path = os.path.join(APPLICATION_DIR, app_id, 'result.html')
            with open(result_path, 'wb') as wb:
                wb.write(html)

            options['state'] = ApplicationState.completed
            options['result'] = '/api/application/{application_id}/result'.format(
                application_id=application_id)
            logging.info('downloading complete')
        else:
            options['state'] = ApplicationState.added

        application = services.update_application(self.db, application.id, options)

        return application
