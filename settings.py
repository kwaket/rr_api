import os
from contextlib import suppress


DATA_DIR = os.path.join(os.getcwd(), 'data')
TASK_DIR = os.path.join(os.getcwd(), 'data', 'tasks')
SAVED_CAPTCHA = os.path.join(os.getcwd(), 'temp', 'captcha')
EGRN_KEY = os.getenv('EGRN_KEY')
COOKIE_DOMAIN = 'rr-api.space'


with suppress(FileExistsError):
    for path in [TASK_DIR, SAVED_CAPTCHA, DATA_DIR]:
        os.makedirs(path)
