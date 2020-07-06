import os
from contextlib import suppress


TASK_DIR = 'tasks'
EGRN_KEY = os.getenv('EGRN_KEY')
COOKIE_DOMAIN = 'rr-api.space'


if __name__ == '__main__':
    with suppress(FileExistsError):
        for path in [TASK_DIR]:
            os.mkdir(path)
