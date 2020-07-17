'''Module define buisneess processes.'''

import os
import glob
from datetime import datetime
import logging
import traceback
from types import FunctionType

from sqlalchemy.orm import Session
import ujson

from spyders import EGRNApplication
import schemas
import models
from settings import APPLICATION_DIR
from db import SessionLocal


class ServiceException(Exception):
    pass


def _extract_filename_without_ext(filepath):
    filename = os.path.split(filepath)[-1]
    return os.path.splitext(filename)[0]


def insert_application_states(db: Session):
    for state in schemas.ApplicationState:
        if not _get_application_state(db, state.name):
            db.add(models.ApplicationState(name=state.name))
            db.commit()


def _get_application_state(db: Session, name: str) -> models.Application:
    return db.query(models.ApplicationState).filter(
        models.ApplicationState.name == name).first()


def _get_application_model(db: Session,
                           application_id: int) -> models.Application:
    return db.query(models.Application).filter(
        models.Application.id == application_id).first()


def _save_application_model(db: Session,
                            model: models.Application) -> models.Application:
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def _update_application_model(db: Session, model: models.Application,
                              updated_fields: dict) -> models.Application:
    model.foreign_id = updated_fields.get('foreign_id', model.foreign_id)
    model.foreign_status = updated_fields.get('foreign_status',
                                              model.foreign_status)
    model.foreign_created = updated_fields.get('foreign_created',
                                               model.foreign_created)
    model.result = updated_fields.get('result', model.result)
    model.updated = datetime.utcnow()
    if updated_fields.get('state'):
        model.state = _get_application_state(db, updated_fields['state'])
    return _save_application_model(db, model)


def add_application(db: Session, cadnum: str) -> schemas.Application:
    model = models.Application(cadnum=cadnum)
    model = _save_application_model(db, model)
    return model.to_schema()


def get_application(db: Session, application_id: int) -> schemas.Application:
    application = db.query(models.Application).filter(
        models.Application.id == application_id).first()
    if not application:
        raise ServiceException('Application does not exist')
    return application.to_schema()


def update_application(db: Session, application_id: int,
                       updated_fields: dict) -> schemas.Application:
    model = _get_application_model(db, application_id)
    if not model:
        raise ServiceException('Application does not exist')
    model = _update_application_model(db, model, updated_fields)
    return model.to_schema()


def get_application_result(db: Session, application_id: int):
    application = get_application(db, application_id)
    if application.foreign_status != 'Завершена':
        raise ServiceException('Result does not ready')
    res = open(os.path.join(APPLICATION_DIR, application.foreign_id,
                            'result.html')).read()
    return res


def get_applications(db: Session, skip: int = 0, limit: int = 10) -> list:
    applications = db.query(models.Application).order_by(
        models.Application.id.desc()).offset(skip).limit(limit).all()
    return [a.to_schema() for a in applications]


def _mark_application_as_error(db: Session, application_id: int):
    application = get_application(db, application_id)
    application.state = schemas.ApplicationState.error
    application = update_application(db, application.id, dict(application))
    return application


def _run_application_with_exception(function: FunctionType,
                                    application_id: int):
    try:
        function(application_id)
    except Exception:
        db = SessionLocal()
        _mark_application_as_error(db, application_id)
        logging.error('spyder exception %s', traceback.format_exc())
    except BaseException:
        db = SessionLocal()
        _mark_application_as_error(db, application_id)
        logging.error('stopped by worker %s', traceback.format_exc())


def order_application(application: schemas.Application):
    '''Order application on rosreestr.ru'''
    logging.info('application added: %s' % str(application))
    spyder = EGRNApplication()
    _run_application_with_exception(spyder.order_application, application.id)
    spyder.close()


def update_application_data(application: schemas.Application):
    '''Update application data (status, result) for rosreestr.ru'''
    logging.info('updating application data: %s' % str(application))
    spyder = EGRNApplication()
    _run_application_with_exception(spyder.update_application_state, application.id)
    spyder.close()
