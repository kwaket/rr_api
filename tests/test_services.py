import pytest
import json
import os
from contextlib import suppress

import services
from settings import APPLICATION_DIR

TASK_ID = '666'

@pytest.fixture
def application_data():
    data = {
        'id': TASK_ID,
        'cadnum': '33:44:555555:33'
    }
    return data


def setup():
    print ("basic setup into module")
    application_data = {
        'id': TASK_ID,
        'cadnum': '33:44:555555:33'
    }
    with open(os.path.join(APPLICATION_DIR, application_data['id'] + '.json'),
              'w') as writer:
        json.dump(application_data, writer)

def teardown():
    print ("basic teardown into module")
    with suppress(FileNotFoundError):
        os.remove(os.path.join(APPLICATION_DIR, TASK_ID + '.json'))


def test_add_application():
    cadnum = '33:44:555555:33'
    result = services.add_application(cadnum)
    assert isinstance(result.id, int)
    assert cadnum == result.cadnum


def test_get_application(application_data):
    result = services.get_application(application_data['id'])
    assert result.cadnum == application_data['cadnum']


def test_update_application(application_data):
    updated_application = application_data.copy()
    updated_application['state'] = 'updating'
    updated = services.update_application(updated_application)
    assert updated.state == 'updating'
    assert updated.id == int(application_data['id'])
