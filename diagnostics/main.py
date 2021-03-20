import os
from glob import glob
import time
from random import randint
from typing import List
from urllib.parse import urljoin
import json
from contextlib import suppress

import requests
import click


DEFAULT_HOST = 'http://localhost:8000'
DATA_DIR = 'data/'


def _get_cadnums(quantity: int) -> List[str]:
    cadnums_example = open('cadnums_example.csv').readlines()
    cadnums: List[str] = []
    length = len(cadnums_example) -1
    while len(cadnums) < quantity:
        cadnums.append(cadnums_example[randint(0, length)])
    cadnums = list(map(lambda x: x.strip(), cadnums))
    print(cadnums)
    return cadnums


def _get_adding_applications() -> List[dict]:
    applications = []
    for filename in glob(DATA_DIR + '*.json'):
        print(filename)
        data = json.load(open(filename))
        if data['state'] in [None, 'adding']:
            applications.append(data)
    return applications


def _save_application(application: dict) -> dict:
    filepath = os.path.join(DATA_DIR, str(application['id']) + '.json')
    with open(filepath, 'w') as wf:
        json.dump(application, wf)
    return application


def order_application(cadnum: str, host: str) -> dict:
    url = urljoin(host, '/api/applications/')
    print(url, cadnum)
    req = requests.post(url, json={'cadnum': cadnum},
                        headers={'access_token': os.getenv('API_KEY')})
    return req.json()


def order_applications(cadnums, host):
    applications = []
    for cadnum in cadnums:
        application = order_application(cadnum, host)
        applications.append(application)
        _save_application(application)
    return applications


def update_application_state(application_id: int, host: str):
    url = urljoin(host, '/api/applications/' + str(application_id))
    result = requests.get(url, headers={'access_token': os.getenv('API_KEY')})
    application = result.json()
    _save_application(application)
    return application


def update_applications_state(host: str):
    applications = _get_adding_applications()
    while applications:
        time.sleep(5)
        for application in applications:
            update_application_state(application['id'], host=host)
        applications = _get_adding_applications()
        print('left:', len(applications), 'applications')


@click.command()
@click.option('--quantity', default=5, help='Количество тестовых заявлений')
@click.option('--host', default=DEFAULT_HOST, help='Хост приложения')
def run_test(quantity, host):
    with suppress(FileExistsError):
        os.mkdir(DATA_DIR)
    cadnums = _get_cadnums(quantity)
    order_applications(cadnums, host=host)
    update_applications_state(host=host)


if __name__ == '__main__':
    run_test()
