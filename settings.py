import os
from contextlib import suppress


DATA_DIR = os.path.join(os.getcwd(), 'data')
TASK_DIR = os.path.join(os.getcwd(), 'data', 'tasks')
APPLICATION_DIR = os.path.join(os.getcwd(), 'data', 'applications')
EXCEPTION_DIR = os.path.join(os.getcwd(), 'temp', 'exceptions')
SAVED_CAPTCHA = os.path.join(os.getcwd(), 'temp', 'captcha')
SAVED_RESPONSES = os.path.join(os.getcwd(), 'temp', 'responses')
EGRN_KEY = os.getenv('EGRN_KEY')
COOKIE_DOMAIN = 'rr-api.space'


for path in [TASK_DIR, SAVED_CAPTCHA, DATA_DIR, SAVED_RESPONSES,
             APPLICATION_DIR, EXCEPTION_DIR]:
    with suppress(FileExistsError):
        os.makedirs(path)
