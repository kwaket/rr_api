from selenium.common.exceptions import WebDriverException

from spyders import EGRNStatement

from pprint import pprint


def execute(task):
    pprint('task added')
    pprint(task)
    spyder = EGRNStatement()
    spyder.get_application(task)
    spyder.close()


def update(task):
    pprint('updating task')
    pprint(task)
    spyder = EGRNStatement()
    spyder.update_application_state(task['id'])
    spyder.close()
