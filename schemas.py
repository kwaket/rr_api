import re
import typing
import json
from datetime import datetime

import os

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


from random import randint





# {
#     "application": {
#         "created": "03.07.2020 15:43",
#         "id": "80-145486932",
#         "status": "Проверка не пройдена  "
#     },
#     "cadnum": "50:26:0100213:15",
#     "id": "2f9bdb1812e0f88175dc86476edfdb35",
#     "inserted": "2020-07-03T15:43:18.573656",
#     "status": "added",
#     "updated": "2020-07-03T16:16:05.676780"
# }

class Application(BaseModel):
    """Application model"""
    id: str = None
    created: datetime = None
    status: str = None
    result: str = None


class Task(BaseModel):
    """Task model"""
    id: str = None
    cadnum: str
    status: str = None
    inserted: datetime = None
    updated: datetime = None
    application: Application = None

    @validator('cadnum')
    def cadnum_must_match_pattern(cls, value):
        res = re.match(r'^[\d]{2}\:[\d]{2}\:[\d]{6,7}\:[\d]{2}$', value)
        if res:
            return value
        raise ValueError('Cadnum must match pattern АА:ВВ:CCCCСCC:КК')
