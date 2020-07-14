'''Module define buisneess processes.'''

import os
import glob
from datetime import datetime

import ujson

from settings import APPLICATION_DIR
from schemas import Application


def _extract_filename_without_ext(filepath):
    filename = os.path.split(filepath)[-1]
    return os.path.splitext(filename)[0]

def _gen_id():
    last = [int(_extract_filename_without_ext(f)[0])
            for f in glob.glob(os.path.join(APPLICATION_DIR, '*.json'))]
    return max(last) + 1


def _gen_filename(application_dir, application_id):
    return os.path.join(application_dir, str(application_id) + '.json')


def _save_application(application: dict) -> Application:
    filepath = _gen_filename(APPLICATION_DIR, application['id'])
    application['id'] = int(application['id'])
    with open(filepath, 'w') as writer:
        ujson.dump(application, writer)
    return Application(**application)


def add_application(cadnum: str) -> Application:
    created = datetime.now().isoformat()
    application = {
        'id': _gen_id(),
        'cadnum': cadnum,
        'inserted': created,
        'updated': created,
        'status': None
    }
    application = _save_application(application)
    return application


def get_application(application_id: str) -> Application:
    filename = _gen_filename(APPLICATION_DIR, application_id)
    return Application(**ujson.load(open(filename)))


def update_application(updated_application: dict) -> Application:
    application = get_application(updated_application['id'])
    application_data = dict(application)
    application_data.update(updated_application)
    if not updated_application.get('updated'):
        application_data['updated'] = datetime.now().isoformat()
    return _save_application(application_data)


def get_application_result(application: dict):
    res = open(os.path.join(APPLICATION_DIR, application['id'],
                            'result.html')).read()
    return res


def get_applications(skip: int, limit: int) -> list:
    applications = glob.glob(os.path.join(APPLICATION_DIR, '*.json'))
    return [Application(**ujson.load(open(f))) for f in applications]
