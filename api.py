import os

from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse
from redis import Redis
from rq import Queue

from schemas import Task
import services
import tasks

queue = Queue(connection=Redis())


API_KEY = os.getenv('API_KEY')
API_KEY_NAME = "access_token"
COOKIE_DOMAIN = "localtest.me"

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


app = FastAPI(title='API для заказа выписок')


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
    response_model=Task
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
    response_model=Task
)
async def update_task_data(task_id: str, api_key: APIKey = Depends(get_api_key)):
    task = services.update_task(
        task_id, {"status": services.TASK_STATUSES['updating']})
    queue.enqueue(tasks.update, task)
    return task

@app.post(
    "/tasks/",
    response_description="Added task with *cadnum* parameter",
    response_model=Task,
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
