import os

from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.responses import HTMLResponse
from redis import Redis
from rq import Queue

from schemas import Task, Application
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
        "name": "tasks",
        "description": "Задачи используются для заказа. Как только выписке будет присвоен номер, он появиться в теле задачи в application",
    }
]

app = FastAPI(title='Rostreestr applications API',
              description="API для заказа выписок c сайта Росреестра",
              version="0.1.1",
              openapi_tags=tags_metadata)


@app.get('/')
async def get_main_page(api_key: APIKey = Depends(get_api_key)):
    return {'name': 'API для заказа выписок'}

# @app.get(
#     "/tasks/",
#     response_description="Tasks",
#     description="Get list of tasks",
#     response_model=list
# )
# async def get_tasks(skip: int = 0, limit: int = 10):
#     try:
#         tasks = get_tasks(skip, limit)
#     except IndexError:
#         raise HTTPException(404, "No such tasks")
#     return tasks


@app.get(
    "/tasks/{task_id}",
    response_description="Task",
    description="Get task from database by id",
    response_model=Task,
    tags=["tasks"]
)
async def get_task(task_id: str, api_key: APIKey = Depends(get_api_key)):
    try:
        task = services.get_task(task_id)
    except IndexError:
        raise HTTPException(404, "No such task")
    return task

@app.get(
    "/tasks/{task_id}/update",
    response_description="Task",
    description="Get task from database by id",
    response_model=Task,
    tags=["tasks"]
)
async def update_task_data(task_id: str, api_key: APIKey = Depends(get_api_key)):
    task = services.update_task(
        task_id, {"status": services.TASK_STATUSES['updating']})
    queue.enqueue(tasks.update, task)
    return task


@app.get(
    "/tasks/{task_id}/application",
    response_description="Application of task",
    description="Get application from taks by task_id",
    response_model=Application,
    tags=["tasks"]
)
async def get_task_application(task_id: str, api_key: APIKey = Depends(get_api_key)):
    try:
        task = services.get_task(task_id)
    except IndexError:
        raise HTTPException(404, "No such task")
    return task.get('application')


@app.get(
    "/tasks/{task_id}/application/result",
    response_description="Result of application",
    description="Get result of application by task_id",
    response_class=HTMLResponse,
    tags=["tasks"]
)
async def get_task_application_result(task_id: str, api_key: APIKey = Depends(get_api_key)):
    try:
        task = services.get_task(task_id)
    except IndexError:
        raise HTTPException(404, "No such task")
    try:
        application_result = services.get_application_result_from_task(task)
    except FileNotFoundError:
        raise HTTPException(404, "Result is not ready")
    return application_result


@app.post(
    "/tasks/",
    response_description="Added task with *cadnum* parameter",
    response_model=Task,
    tags=["tasks"]
)
async def add_task(task: Task, api_key: APIKey = Depends(get_api_key)):
    task = services.add_task(task.cadnum)
    queue.enqueue(tasks.execute, task)
    return task


# @app.put(
#     "/tasks/{task_id}",
#     response_description="Update task with *id*",
#     response_model=Task,
# )
# async def update_task(task_id: str, task: Task, api_key: APIKey = Depends(get_api_key)):
#     task = services.update_task(task_id, task.dict())
#     return task
