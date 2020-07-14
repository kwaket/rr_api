import os

from fastapi.testclient import TestClient
import pytest

from api import app

client = TestClient(app)


TASK_ID = '666'


@pytest.fixture
def application_data():
    data = {
        'id': TASK_ID,
        'cadnum': '50:26:0100213:15'
    }
    return data


def test_auth():
    response = client.get("/api/")
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}
    response = client.get("/api/", headers={"access_token": "wrong"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}
    response = client.get("/api/", headers={"access_token": os.getenv('API_KEY')})
    assert response.status_code == 200
    assert response.json() == {'name': 'API для заказа выписок'}


def test_add_application():
    global TASK_ID
    response = client.post(
        "/api/applications/",
        headers={"access_token": os.getenv('API_KEY')},
        json={"cadnum": "50:26:0100213:15"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["cadnum"] == "50:26:0100213:15"
    assert result["id"]
    assert result["updated"]
    TASK_ID = result["id"]


def test_get_application():
    response = client.get(
        "/api/applications/" + str(TASK_ID),
        headers={"access_token": os.getenv('API_KEY')}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["cadnum"] == "50:26:0100213:15"
    assert result["id"] == TASK_ID
    assert result["inserted"]
    assert result["updated"]


# def test_update_application():
#     data = {
#         "cadnum": "50:26:0100213:15",
#         "id": TASK_ID,

#         "foreign_id": "20-231432",
#         "foreign_status": "В работе",
#         "result": None
#     }
#     response = client.put(
#         "/api/applications/" + str(TASK_ID),
#         headers={"access_token": os.getenv('API_KEY')},
#         json=data
#     )
#     assert response.status_code == 200
#     result = response.json()
#     assert result["cadnum"] == "50:26:0100213:15"
#     assert result["id"] == TASK_ID
#     assert result["foreign_id"] == data["foreign_id"]
#     assert result["foreign_status"] == data["foreign_status"]
#     assert result["result"] is None
