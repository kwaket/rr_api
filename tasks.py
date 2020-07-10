import logging

from selenium.common.exceptions import WebDriverException

from spyders import EGRNStatement

from pprint import pprint


import services


def _run_task_with_exception(function, task):
    try:
        function(task)
    except BaseException as exc:
        services.update_task(task['id'], {"status": "error"})
        logging.error('stopped by worker %s', str(exc))



def execute(task):
    pprint('task added')
    pprint(task)
    spyder = EGRNStatement()
    _run_task_with_exception(spyder.get_application, task)
    # try:
    #     spyder.get_application(task)
    # except BaseException:
    #     update_task(task['id'], {"status": "error"})
    spyder.close()


def update(task):
    pprint('updating task')
    pprint(task)
    spyder = EGRNStatement()
    _run_task_with_exception(spyder.update_application_state, task)
    # try:
    #     spyder.update_application_state(task['id'])
    # except BaseException:
    #     update_task(task['id'], {"status": "error"})
    spyder.close()
