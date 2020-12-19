import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.services as services
from app.schemas import Application
import app.models as models
from app.db import Base


SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_TEST_URL')

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    try:
        db = TestingSessionLocal()
        application = models.Application(cadnum='33:44:555555:33')
        db.add(application)
        db.commit()

        services.insert_application_states(db)
        yield db
    finally:
        db.close()


@pytest.fixture
def application_data(db):
    application = db.query(models.Application).first()
    data = {
        'id': application.id,
        'cadnum': application.cadnum
    }
    return data


def test_add_application(db):
    cadnum = '33:44:555555:33'
    result = services.add_application(db, cadnum)
    assert isinstance(result.id, int)
    assert cadnum == result.cadnum


def test_get_application(db, application_data):
    result = services.get_application(db, application_data['id'])
    assert result.cadnum == application_data['cadnum']


def test_update_application(db, application_data):
    updated_application = application_data.copy()
    updated_application['state'] = 'updating'
    updated = services.update_application(db, updated_application['id'],
                                          updated_application)
    assert updated.state == 'updating'
    assert updated.id == application_data['id']


def test_get_applications(db):
    applications = services.get_applications(db, 0, 10)
    assert isinstance(applications, list)
    assert isinstance(applications[0], Application)
