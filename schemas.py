'''Module define data models for validation and serialization.'''

import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, validator


class ApplicationState(str, Enum):
    adding = 'adding'
    added = 'added'
    updating = 'updating'
    updated = 'updated'
    completed = 'completed'
    error = 'error'


class Application(BaseModel):
    """Application model"""
    id: int = None  # "идентефикатор приложения (АПИшки)"
    cadnum: str  # "кадастровый номер по которому делается выписка"
    foreign_id: str = None  # "номер выписки (росреестровский)"
    foreign_status: str = None  # "статус выписки (росреестровский)"
    foreign_created: str = None # "время создания выписки (росреестровское)"
    result: str = None  # "null или ссылка на html результат"
    inserted: datetime = None
    updated: datetime = None  # "дата обновления (актуализации) данных с росреестра"
    state: ApplicationStatus = None

    @validator('cadnum')
    def cadnum_must_match_pattern(cls, value):
        res = re.match(r'^[\d]{2}\:[\d]{2}\:[\d]{6,7}\:[\d]{1,}$', value)
        if res:
            return value
        raise ValueError('Cadnum must match pattern АА:ВВ:CCCCСCC:КК')
