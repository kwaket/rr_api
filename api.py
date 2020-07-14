import os

from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.responses import HTMLResponse
from redis import Redis
from rq import Queue

from schemas import Application, ApplicationStatus
import services
import tasks
from settings import COOKIE_DOMAIN


queue = Queue(connection=Redis())


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
    response_model=list,
    tags=["applications"]
)
async def get_applications(skip: int = 0, limit: int = 10,
                           api_key: APIKey = Depends(get_api_key)):
    try:
        applications = services.get_applications(skip, limit)
    except IndexError:
        raise HTTPException(404, "No such applications")
    return applications


@app.get(
    "/api/applications/{application_id}",
    response_description="Application",
    description="Получить заявление по id",
    response_model=Application,
    tags=["applications"]
)
async def get_application(application_id: str,
                          api_key: APIKey = Depends(get_api_key)):
    try:
        application = services.get_application(application_id)
    except FileNotFoundError:
        raise HTTPException(404, "No such application")
    return application

@app.get(
    "/api/applications/{application_id}/update",
    response_description="Application",
    description="""Обновить данные заявления по id.
        Время обновления данных около 2 минут""",
    response_model=Application,
    tags=["applications"]
)
async def update_application_data(application_id: str,
                                  api_key: APIKey = Depends(get_api_key)):
    application = services.update_application(
        {"id": application_id, "status": ApplicationStatus.updating})
    queue.enqueue(tasks.update, application)
    return application


@app.get(
    "/api/applications/{application_id}/result",
    response_description="Result of application",
    description="""Получить результат заявления по id.
        Доступно если статус заявления **Завершено**""",
    response_class=HTMLResponse,
    tags=["applications"]
)
async def get_application_result(application_id: str,
                                 api_key: APIKey = Depends(get_api_key)):
    try:
        application = services.get_application(application_id)
    except FileNotFoundError:
        raise HTTPException(404, "No such task")
    try:
        application_result = services.get_application_result(application)
    except FileNotFoundError:
        raise HTTPException(404, "Result is not ready")
    return application_result


@app.post(
    "/api/applications/",
    response_description="Added task with *cadnum* parameter",
    description="""Заказать выписку. Обязательный параметр **cadnum**.
        В результе запроса заявлению будет присвоен id (внутренний)
        для дальнейшего отслеживания статуса заявления.
        Время получения номера заявления около 2 минут""",
    response_model=Application,
    tags=["applications"]
)
async def add_application(application: Application,
                          api_key: APIKey = Depends(get_api_key)):
    application = services.add_application(application.cadnum)
    queue.enqueue(tasks.execute, application)
    return application
