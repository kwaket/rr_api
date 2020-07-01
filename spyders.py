import os
import json
from contextlib import suppress
import time
import logging

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException,\
    NoSuchElementException
from PIL import Image

from recognizer import recognize


SERVICE_URL = 'https://rosreestr.ru/wps/portal/online_request'
SAVED_CAPTCHA = 'temp'
DATA_DIR = 'data'
NOT_FOUND_LIST = 'not_found.txt'
# ERRORS_LIST = 'errors.txt'


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
        task_id = args[0].task_id
        logging.info('{task_id}: start {func_name}'.format(task_id=task_id, func_name=func.__name__))
        res = func(*args, **kwargs)
        logging.info('{task_id}: end {func_name}'.format(task_id=task_id, func_name=func.__name__))
        return res
    return wrapper


class EGRNBase():

    # @logger
    def __init__(self, task_id):
        self.driver = webdriver.Chrome()
        self._set_task_id(task_id)

    # @logger
    def _set_task_id(self, task_id):
        self.task_id = task_id
        return self.task_id

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
        elem = None
        while timeout > 0:
            try:
                elem = self.driver.find_element_by_xpath(xpath)
            except NoSuchElementException as exc:
                print(exc)
                time.sleep(1)
                timeout -= 1
            else:
                break
        if elem:
            return elem
        raise NoSuchElementException()

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

    def __init__(self, task_id=None, egrn_key=None):
        EGRNBase.__init__(self, task_id)
        self.egrn_key = egrn_key or os.getenv('EGRN_KEY_SAV')  ## or os.getenv('EGRN_KEY') @@@@@@@@@@@@@@@@@@@@@@@@@@@@@!!!!!!!!!!!
        self.is_auth = False
        self.regions = json.load(open('regions.json'))  # https://rosreestr.ru/wps/portal/cc_ib_OpenData?param_infoblock_document_path=openData_region.htm

    @logger
    def login(self):
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

        # key_fields[-1].send_keys(webdriver.common.keys.Keys.RETURN)
        time.sleep(1)
        self.driver.find_element_by_xpath('//span[text()="Войти"]').click()

        next_page_elem = self._wait_element(
            '//span[text()="Поиск объектов недвижимости"]', timeout=20)
        self.is_auth = bool(next_page_elem)
        while not self.is_auth:
            time.sleep(3)
            logging.info('trying to logging again')
            self.login()

    @logger
    def get_statement(self, cadnum):
        if not self.is_auth:
            self.login()
            time.sleep(5)
            print('login succes')
        else:
            self._go('https://rosreestr.ru/wps/portal/p/cc_present/ir_egrn')
        import ipdb; ipdb.set_trace()

        self._wait_and_click('//span[text()="Поиск объектов недвижимости"]',
            timeout=10)
        self._wait_element('//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input',
            timeout=20)
        fields = self.driver.find_elements_by_xpath('//*[@id="v-Z7_01HA1A42KODT90AR30VLN22003"]//input')
        cadnum_field = fields[0]
        region_field = fields[2]

        cadnum_field.send_keys(cadnum)

        region = self._get_region(cadnum)
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
        while captcha_field.get_property('value') != code:
            captcha_field.clear()
            captcha_field.send_keys(code)
            time.sleep(1)

        self._wait_and_click('//span[text()="Отправить запрос"]')

        # Всплывающее окно
        ## Номер заявки
        popup_element = self._wait_element('//div[@class="popupContent"]')
        result_element = self._wait_element('.//b', 5)
        if result_element:
            request_number = result_element.text
            print(request_number)
        else:
            message = self._wait_element('//div[@class="popupContent"]').text
            logging.warning(message)
            print(message)
        ## Продолжить работу
        self.driver.find_element_by_xpath('//span[text()="Продолжить работу"]').click()

        # import ipdb; ipdb.set_trace()
        # print('OK', cadnum)

    def _get_region(self, cadnum):
        return self.regions[cadnum.split(':')[0]]





class EGRNSpyder():

    def __init__(self):
        # self.driver = webdriver.Chrome()
        self.driver.set_page_load_timeout(30)

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

    def get_info(self, cadnum):
        links = self._find_object(cadnum)
        data = self._grab_data_sources(links)
        if not data:
            with open(NOT_FOUND_LIST, 'a') as f:
                f.write(cadnum)
        return data

    def save_info(self, cadnum):
        data = self.get_info(cadnum)
        if data:
            json.dump(data, open(self._gen_filename(data[0]), 'w'))

    def close(self):
        with suppress(WebDriverException):
            self.driver.close()

    @staticmethod
    def _gen_filename(data):
        cn = data['Кадастровый номер']
        filename = cn.replace(':', '_') + '.json'
        return os.path.join(DATA_DIR, filename)

    def _fill_capthca(self, next_picture=False):
        if next_picture:
            print('Повторный ввод кода')
            self.driver.execute_script('changeCaptcha()')
            time.sleep(.5)
        captcha = self.driver.find_element_by_id('captchaImage2')
        code = self._recognize_captcha(captcha)
        while not code:
            print('trying to get code again...')
            time.sleep(1)
            self.driver.execute_script('changeCaptcha()')
            time.sleep(1)
            captcha = self.driver.find_element_by_id('captchaImage2')
            code = self._recognize_captcha(captcha)

        field = self.driver.find_element_by_name('captchaText')
        field.clear()

        print(code, type(code))
        field.send_keys(code)
        # time.sleep(.5)


        ## Move chechink captcha here !!!!

        return code

    # def _get_captcha_code(self)

    def _get_form_message(self):
        mess = self.driver.find_element_by_xpath('//td[@class="infomsg1"]//span')
        return mess.text

    def _find_object(self, cadnum):
        self._go(SERVICE_URL)
        field = self.driver.find_element_by_name('cad_num')
        field.clear()
        field.send_keys(cadnum)

        self._fill_capthca()
        self.driver.find_element_by_id('submit-button').click()

        results = self.driver.find_elements_by_xpath(
            '//table//table//td/a[not(contains(@href, "javascript"))]')
        if not results:
            msg = self._get_form_message()

            if msg.startswith('Текст с картинки введен неверно'):
                print('Код введен неверно')

            while msg.startswith('Текст с картинки введен неверно'):

                print('Попытка ввода заново...')

                self._fill_capthca(next_picture=True)
                self.driver.find_element_by_id('submit-button').click()
                msg = self._get_form_message()


            results = self.driver.find_elements_by_xpath(
                '//table//table//td/a[not(contains(@href, "javascript"))]')

        result_links = [r.get_attribute('href') for r in results]
        return result_links

    def _grab_data_sources(self, links):
        data = []
        for url in links:
            data.append(self._grab_data_source(url))
        return data

    def _grab_data_source(self, url):
        self._go(url)
        table = self.driver.find_elements_by_xpath(
            '//div[@class="portlet-body"]//table/tbody/tr')

        data = []
        for row in table:
            data.append(row.find_elements_by_tag_name('td'))
        data = {clean_key(r[0].text): r[1].text for r in data if len(r) == 2}
        data = {k: v for k, v in data.items() if k}
        return data

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

    def _save_captcha(self, element):
        filename = os.path.join(SAVED_CAPTCHA, element.id + '.png')
        return self._take_screenshot(element, filename)
