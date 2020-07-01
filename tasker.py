import json
import time
import logging
import traceback

import redis
import click
from selenium.common.exceptions import WebDriverException

from spyders import EGRNSpyder
from services import push_result


logging.basicConfig(
    format='%(filename)s %(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO)


def run_spyder():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    p = r.pubsub()
    p.subscribe('tasks-channel')

    spyder = EGRNSpyder()

    while True:
        task = p.get_message()
        if task and task.get('type') == 'message':
            task = json.loads(task['data'])
            logging.info('Start to execute task ' + task['id'])
            try:
                task['data'] = spyder.get_info(task['cadnum'])
            except WebDriverException:
                spyder.close()
                spyder = EGRNSpyder()
                task['data'] = spyder.get_info(task['cadnum'])

            push_result(r, task)
        time.sleep(1)
        # logging.info('No task to execute')


if __name__ == '__main__':
    run_spyder()
