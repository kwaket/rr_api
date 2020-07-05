import os
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

TASK_ID = None


def test_auth():
    response = client.get("/")
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}
    response = client.get("/", headers={"access_token": "wrong"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}
    response = client.get("/", headers={"access_token": os.getenv('API_KEY')})
    assert response.status_code == 200
    assert response.json() == {'name': 'API для заказа выписок'}


def test_add_task():
    global TASK_ID
    response = client.post(
        "/tasks/",
        headers={"access_token": os.getenv('API_KEY')},
        json={"cadnum": "50:26:0100213:15"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["cadnum"] == "50:26:0100213:15"
    assert result["id"]
    assert result["inserted"]
    assert result["updated"]
    TASK_ID = result["id"]


def test_get_task():
    response = client.get(
        "/tasks/" + TASK_ID,
        headers={"access_token": os.getenv('API_KEY')}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["cadnum"] == "50:26:0100213:15"
    assert result["id"] == TASK_ID
    assert result["inserted"]
    assert result["updated"]


# def test_update_task():
#     data = {
#         "cadnum": "50:26:0100213:15",
#         "id": TASK_ID,
#         "application": {
#             "id": "20-231432",
#             "status": "В работе",
#             "result": None
#         }
#     }
#     response = client.put(
#         "/tasks/" + TASK_ID,
#         headers={"access_token": os.getenv('API_KEY')},
#         json=data
#     )
#     assert response.status_code == 200
#     result = response.json()
#     assert result["cadnum"] == "50:26:0100213:15"
#     assert result["id"] == TASK_ID
#     assert result["application"]["id"] == data["application"]["id"]
#     assert result["application"]["status"] == data["application"]["status"]
#     assert result["application"]["result"] is None
