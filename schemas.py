import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, validator


class ApplicationStatus(str, Enum):
    adding = 'adding'
    added = 'added'
    updating = 'updating'
    update = 'updated'
    error = 'error'


class Application(BaseModel):
    """Application model"""
    id: int = None  # "идентефикатор приложения (АПИшки)"
    cadnum: str  # "кадастровый номер по которому делается выписка"
    foreign_id: str = None  # "номер выписки (росреестровский)"
    foreing_status: str = None  # "статус выписки (росреестровский)"
    foreing_created: str = None # "время создания выписки (росреестровское)"
    result: str = None  # "null или ссылка на html результат"
    created: datetime = None
    updated_at: datetime = None  # "дата обновления (актуализации) данных с росреестра"
    state: ApplicationStatus = None

    @validator('cadnum')
    def cadnum_must_match_pattern(cls, value):
        res = re.match(r'^[\d]{2}\:[\d]{2}\:[\d]{6,7}\:[\d]{1,}$', value)
        if res:
            return value
        raise ValueError('Cadnum must match pattern АА:ВВ:CCCCСCC:КК')
