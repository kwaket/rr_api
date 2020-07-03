'''Module define buisneess processes.'''

import os
import json
import hashlib
from datetime import datetime

from settings import TASK_DIR


TASK_STATUSES = {
    "adding": "adding",
    "added": "added",
    "updating": "updating",
    "completed": "completed",
    "error": "error"
}

def _gen_id():
    hsh = hashlib.md5(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f").encode('utf8'))
    return hsh.hexdigest()


def _gen_filename(task_dir, task_id):
    return os.path.join(task_dir, task_id + '.json')


def _save_task(task: dict) -> dict:
    filepath = _gen_filename(TASK_DIR, task['id'])
    with open(filepath, 'w') as writer:
        json.dump(task, writer)
    return task


def add_task(cadnum):
    task_id = _gen_id()
    task = {
        'id': task_id,
        'cadnum': cadnum,
        'inserted': datetime.now().isoformat(),
        'updated': None,
        'status': None
    }
    task = _save_task(task)
    return task


def get_task(task_id: str) -> dict:
    filename = _gen_filename(TASK_DIR, task_id)
    return json.load(open(filename))


def update_task(task_id: str, updated_options: dict) -> dict:
    task = get_task(task_id)
    task.update(updated_options)
    if not updated_options.get('updated'):
        task['updated'] = datetime.now().isoformat()
    return _save_task(task)
