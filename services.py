import time
import json
import logging
import hashlib
from datetime import datetime


def get_result(r, task_id):
    res = _get_results(r).get(task_id)
    if res:
        remove_result(r, task_id)
    return res


def _get_results(r):
    res = r.get('results')
    return json.loads(res) if res else {}


def _update_results(r, results_dict):
    r.set('results', json.dumps(results_dict))
    return results_dict


def push_result(r, task):
    '''Push result of task with the same id.'''
    logging.info('Push result of task ' + task['id'])
    results = _get_results(r)
    results[task['id']] = task
    return _update_results(r, results)


def remove_result(r, task_id):
    '''Remove result of task.'''
    logging.info('Remove result of task ' + task_id)
    results = _get_results(r)
    del results[task_id]
    return _update_results(r, results)


def gen_id():
    h = hashlib.md5(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f").encode('utf8'))
    return h.hexdigest()


def get_obj_data(r, cadnum):
    task_id = gen_id()
    task = {
        'id': task_id,
        'cadnum': cadnum
    }
    r.publish('tasks-channel', json.dumps(task))

    result = get_result(r, task_id)
    while not result:
        time.sleep(1)
        result = get_result(r, task_id)
    return result
