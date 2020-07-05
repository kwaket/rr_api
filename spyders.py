import os
import json
from contextlib import suppress
import time
import logging

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from recognizer import recognize

import services
from services import TASK_STATUSES
from settings import EGRN_KEY


SERVICE_URL = 'https://rosreestr.ru/wps/portal/online_request'
SAVED_CAPTCHA = 'temp'
DATA_DIR = 'data'


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


with suppress(FileExistsError):
    for path in [SAVED_CAPTCHA, DATA_DIR]:
        os.mkdir(path)


def clean_key(word):
    if word.endswith(':'):
        word = word[:-1]
    return word.strip()


def logger(func):
    def wrapper(*args, **kwargs):
        task_id = args[0].current_task_id or 'Out of task'
        logging.info('%s: start %s. Args: %s, kwargs, %s', task_id,
                     func.__name__, str(args), str(kwargs))
        res = func(*args, **kwargs)
        logging.info('%s: end %s', task_id, func.__name__)
        return res
    return wrapper


class EGRNBase():

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        self.current_task_id = None

    def _set_task_id(self, task_id):
        self.current_task_id = task_id
        return self.current_task_id

    @logger
    def close(self):
        with suppress(WebDriverException):
            self.driver.close()

    @logger
    def _go(self, url):
        # return self.driver.get(url)
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


class EGRNStatement(EGRNBase):

    def __init__(self, egrn_key=None):
        EGRNBase.__init__(self)
        self.egrn_key = egrn_key or EGRN_KEY
        self.is_auth = False
        self.regions = json.load(open('regions.json'))

    @logger
    def login(self):
        self._login()
        next_page_elem = self._wait_element(
            '//span[text()="Поиск объектов недвижимости"]', timeout=10)

        self.is_auth = bool(next_page_elem)
        attempts = 5
        while not self.is_auth and attempts:
            logging.warning('next_page_elem: %s\n', str(next_page_elem))
            time.sleep(3)
            logging.warning('trying to logging again')
            self._login()
            next_page_elem = self.driver.find_elements_by_xpath(
                '//span[text()="Поиск объектов недвижимости"]')
            if next_page_elem:
                self.is_auth = True
            attempts -= 1
        else:
            return True
        raise WebDriverException

    def _login(self):
        self._go('https://rosreestr.ru/wps/portal/p/cc_present/ir_egrn')
        self._wait_element('.//div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input', 5)
        key_fields = self.driver.find_elements_by_xpath(
            './/div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')

        for field, part in zip(key_fields, self.egrn_key.split('-')):
            field.send_keys(part)
            time.sleep(1)

        _key_fields = self.driver.find_elements_by_xpath(
            './/div[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        _key = '-'.join([k.text for k in _key_fields])
        assert _key != self.egrn_key
        time.sleep(1)
        self.driver.find_element_by_xpath('//span[text()="Войти"]').click()

    @logger
    def get_application(self, task):
        self._set_task_id(task['id'])
        task = services.update_task(task['id'], {'status': TASK_STATUSES['adding']})
        if not self.is_auth:
            self.login()
            time.sleep(5)
            print('login succes')
        else:
            self._go('https://rosreestr.ru/wps/portal/p/cc_present/ir_egrn')

        self._wait_and_click('//span[text()="Поиск объектов недвижимости"]',
                             timeout=10)
        self._wait_element('//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input',
                           timeout=20)
        fields = self.driver.find_elements_by_xpath('//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        cadnum_field, region_field = fields[0], fields[2]
        cadnum_field.send_keys(task['cadnum'])
        region = self._get_region(task['cadnum'])
        region_field.send_keys(region)
        self._wait_element('//*[@id="VAADIN_COMBOBOX_OPTIONLIST"]')
        xpath = '//*[@id="VAADIN_COMBOBOX_OPTIONLIST"]//*[text()="{}"]'
        self._click_by(xpath.format(region))

        self.driver.find_element_by_xpath('//span[text()="Найти"]').click()

        self._wait_and_click('//td[contains(@class, "v-table-cell-content-cadastral_num")]')

        captcha_pic = self._wait_element('//img[contains(@src, "captcha")]')

        code = self._recognize_captcha(captcha_pic)
        captcha_field = self.driver.find_element_by_xpath(
            '//div[@name="ibmMainContainer"]//input[@type="text"]')
        time.sleep(1)
        while captcha_field.get_property('value') != code:
            captcha_field.clear()
            captcha_field.send_keys(code)
            time.sleep(3)

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
        logging.warning('result %s', result_elements)
        if result_elements:
            application_id = result_elements.text
            # print(application)
            task = services.update_task(task['id'], {
                'application': {'id': application_id},
                'status': TASK_STATUSES['added']})
            logging.warning('Got application id %s', application_id )
        else:
            message = self._wait_element('//div[@class="popupContent"]').text
            logging.warning(message)
            task = services.update_task(task['id'], {
                'status': TASK_STATUSES['error'],
                'message': str(message)})

        ## Продолжить работу
        self.driver.find_element_by_xpath('//span[text()="Продолжить работу"]').click()

        return task

    @logger
    def update_application_state(self, task_id):
        self._set_task_id(task_id)
        task = services.get_task(task_id)

        services.update_task(task_id, {'status': TASK_STATUSES['updating']})
        if not self.is_auth:
            self.login()
            time.sleep(5)
            print('login succes')
        else:
            self._go('https://rosreestr.ru/wps/portal/p/cc_present/ir_egrn')

        self._wait_and_click('//span[text()="Мои заявки"]', timeout=10)

        filter_input = self.driver.find_element_by_class_name('v-textfield')
        filter_input.send_keys(task['application']['id'])

        self._wait_and_click('//span[text() = "Обновить"]')

        main_block = self.driver.find_element_by_class_name('v-app')
        results = main_block.find_elements_by_class_name('v-table-table')
        if not results:
            raise ValueError('Too much or too few results found')

        cells = results[0].find_elements_by_xpath('.//td')

        app_id, app_created, app_status = [c.text for c in cells[:3]]
        options = {'application': {
            'id': app_id,
            'created': datetime.strptime(
                app_created, '%d.%m.%Y %H:%M').isoformat(),
            'status': app_status}}

        if app_status == 'Завершена':
            print('downloading')
            options['status'] = TASK_STATUSES['completed']
            options['application']['result'] = 'results'
        else:
            options['status'] = TASK_STATUSES['added']

        task = services.update_task(task_id, options)

        return task

    def _get_region(self, cadnum):
        return self.regions[cadnum.split(':')[0]]
