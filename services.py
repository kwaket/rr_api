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
    last = [int(_extract_filename_without_ext(f))
            for f in glob.glob(os.path.join(APPLICATION_DIR, '*.json'))]
    return max(last) + 1


def _gen_filename(application_dir: str, application_id: int):
    return os.path.join(application_dir, str(application_id) + '.json')


def _save_application(application: Application) -> Application:
    filepath = _gen_filename(APPLICATION_DIR, application.id)
    application_dict: dict = dict(application)
    for k, v in application_dict.items():
        if isinstance(v, datetime):
            application_dict[k] = v.isoformat()
    with open(filepath, 'w') as writer:
        ujson.dump(application_dict, writer)
    return Application(**application_dict)


def add_application(cadnum: str) -> Application:
    created = datetime.utcnow().isoformat()
    application = {
        'id': _gen_id(),
        'cadnum': cadnum,
        'inserted': created,
        'updated': created,
        'status': None
    }
    return _save_application(Application(**application))


def get_application(application_id: int) -> Application:
    filename = _gen_filename(APPLICATION_DIR, application_id)
    return Application(**ujson.load(open(filename)))


def update_application(application_id: int,
                       updated_fields: dict) -> Application:
    application = get_application(application_id)
    application_data = dict(application)
    application_data.update(updated_fields)
    if not application.updated:
        application_data['updated'] = datetime.utcnow().isoformat()
    return _save_application(Application(**application_data))


def get_application_result(application: Application):
    res = open(os.path.join(APPLICATION_DIR, str(application.id),
                            'result.html')).read()
    return res


def get_applications(skip: int, limit: int) -> list:
    applications = glob.glob(os.path.join(APPLICATION_DIR, '*.json'))
    return [Application(**ujson.load(open(f))) for f in applications]
