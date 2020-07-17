'''Module define data models for validation and serialization.'''

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator


class ApplicationState(str, Enum):
    """Модель описывает состояние заявления в API."""
    adding = 'adding'
    added = 'added'
    updating = 'updating'
    updated = 'updated'
    completed = 'completed'
    error = 'error'


class Application(BaseModel):
    """Модель заявления.

    Поля id, cadnum, inserted, updated, state определяются текущим API:
      * id - внутренний идентефикатор заявления
      * cadnum - кадастровый номер по которому делается заявление
      * inserted - время вставки (создания) заявления
      * updated - время последнего обновления (актуализиции) заявления
      * state - состояние

    Поля foreign_id, foreign_status, foreign_created, result представляют
    поля выписки с сайта Росреестра:
      * foreign_id - номер выписки
      * foreign_status - статус выписки
      * foreign_created - время создания выписки
      * result - ссылка на html результат или пустое значение если результат не готов
    """
    id: int
    cadnum: str
    foreign_id: Optional[str] = None
    foreign_status: Optional[str] = None
    foreign_created: Optional[datetime] = None
    result: Optional[str] = None
    inserted: Optional[datetime] = None
    updated: Optional[datetime] = None
    state: Optional[ApplicationState] = None

    @validator('cadnum')
    def cadnum_must_match_pattern(cls, value):
        res = re.match(r'^[\d]{2}\:[\d]{2}\:[\d]{6,7}\:[\d]{1,}$', value)
        if res:
            return value
        raise ValueError('Cadnum must match pattern АА:ВВ:CCCCСCC:КК')
