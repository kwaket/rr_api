import os
from typing import List

from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.responses import HTMLResponse

import services
from settings import COOKIE_DOMAIN
import schemas
from db import SessionLocal


app = FastAPI()
queue = Queue(connection=Redis(), default_timeout=3600)
queue_low = Queue('low', connection=Redis(), default_timeout=3600)


API_KEY = os.getenv('API_KEY')
API_KEY_NAME = "access_token"
COOKIE_DOMAIN = COOKIE_DOMAIN

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_query: str = Security(api_key_query),
                      api_key_header: str = Security(api_key_header),
                      api_key_cookie: str = Security(api_key_cookie)):
    if api_key_query == API_KEY:
        return api_key_query
    if api_key_header == API_KEY:
        return api_key_header
    if api_key_cookie == API_KEY:
        return api_key_cookie
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


tags_metadata = [
    {
        "name": "applications",
        "description": """В заявлениях используется id назначаемый приложением.
            Внешний id (номер заявления) присваивается в течении 1 минуты в поле **foreign_id**""",
    }
]

app = FastAPI(title='Rostreestr applications API',
              description="API для заказа выписок c сайта Росреестра",
              version="0.2.0",
              openapi_tags=tags_metadata)


@app.get('/api')
async def get_main_page(api_key: APIKey = Depends(get_api_key)):
    return {'name': 'API для заказа выписок'}


@app.get(
    "/api/applications/",
    response_description="applications",
    description="Получить список заявлений",
    response_model=List[schemas.Application],
    tags=["applications"]
)
async def get_applications(skip: int = 0, limit: int = 10,
                           db: Session = Depends(get_db),
                           api_key: APIKey = Depends(get_api_key)):
    applications = services.get_applications(db, skip, limit)
    return applications


@app.get(
    "/api/applications/{application_id}",
    response_description="Application",
    description="Получить заявление по id",
    response_model=schemas.Application,
    tags=["applications"]
)
async def get_application(application_id: int,
                          db: Session = Depends(get_db),
                          api_key: APIKey = Depends(get_api_key)):
    try:
        application = services.get_application(db, application_id)
    except services.ServiceException as exc:
        raise HTTPException(404, str(exc))
    return application


@app.get(
    "/api/applications/{application_id}/update",
    response_description="Application",
    description="""Обновить данные заявления по id.
        Время обновления данных около 2 минут""",
    response_model=schemas.Application,
    tags=["applications"]
)
async def update_application_data(application_id: int,
                                  db: Session = Depends(get_db),
                                  api_key: APIKey = Depends(get_api_key)):
    application = services.update_application(db, application_id,
                                              {"status": schemas.ApplicationState.updating})
    queue.enqueue(services.update_application_data, application)
    return application


@app.get(
    "/api/applications/{application_id}/result",
    response_description="Result of application",
    description="""Получить результат заявления по id.
        Доступно если статус заявления **Завершено**""",
    response_class=HTMLResponse,
    tags=["applications"]
)
async def get_application_result(application_id: int,
                                 db: Session = Depends(get_db),
                                 api_key: APIKey = Depends(get_api_key)):
    try:
        application_result = services.get_application_result(db, application_id)
    except services.ServiceException as exc:
        raise HTTPException(404, str(exc))
    return application_result


@app.post(
    "/api/applications/",
    response_description="Added task with *cadnum* parameter",
    description="""Заказать выписку. Обязательный параметр **cadnum**.
        В результе запроса заявлению будет присвоен id (внутренний)
        для дальнейшего отслеживания статуса заявления.
        Время получения номера заявления около 2 минут""",
    response_model=schemas.Application,
    tags=["applications"]
)
async def add_application(application: schemas.Application,
                          db: Session = Depends(get_db),
                          api_key: APIKey = Depends(get_api_key)):
    try:
        application = services.add_application(db, application.cadnum)
    except services.ServiceException as exc:
        raise HTTPException(500, "Server error. Failed to order application")
    queue.enqueue(services.order_application, application)
    queue_low.enqueue(services.update_application_data, application)
    return application


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)

