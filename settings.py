import os
from contextlib import suppress


DATA_DIR = os.path.join(os.getcwd(), 'data')
APPLICATION_DIR = os.path.join(os.getcwd(), 'data', 'applications')
EXCEPTION_DIR = os.path.join(os.getcwd(), 'temp', 'exceptions')
SAVED_CAPTCHA = os.path.join(os.getcwd(), 'temp', 'captcha')
SAVED_RESPONSES = os.path.join(os.getcwd(), 'temp', 'responses')
EGRN_KEY = os.getenv('EGRN_KEY')
COOKIE_DOMAIN = 'rr-api.space'
SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')


for path in [SAVED_CAPTCHA, DATA_DIR, SAVED_RESPONSES,
             APPLICATION_DIR, EXCEPTION_DIR]:
    with suppress(FileExistsError):
        os.makedirs(path)
