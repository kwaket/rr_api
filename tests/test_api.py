import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.api import app, get_db


SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


TASK_ID = None


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
    assert result["inserted"]
    TASK_ID = result["id"]


def test_get_application():
    response = client.get(
        "/api/applications/" + str(TASK_ID),
        headers={"access_token": os.getenv('API_KEY')}
    )
    assert response.status_code == 200
    result = response.json()
    print(result)
    assert result["cadnum"] == "50:26:0100213:15"
    assert result["id"] == TASK_ID
    assert result["inserted"]


def test_get_applications():
    response = client.get(
        "/api/applications/",
        headers={"access_token": os.getenv('API_KEY')}
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
