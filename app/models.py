'''Module define data models for storing in database.'''
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base
import app.schemas as schemas


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    cadnum = Column(String(100))  # add validator
    foreign_id = Column(String(20), unique=True)
    foreign_status = Column(String(100))
    foreign_created = Column(DateTime())
    result = Column(String)
    inserted = Column(DateTime())
    updated = Column(DateTime())

    state_id = Column(Integer, ForeignKey('applications_states.id'))
    state = relationship('ApplicationState', back_populates="application")

    def to_schema(self) -> schemas.Application:
        return schemas.Application(**{
            "id": self.id,
            "cadnum": self.cadnum,
            "foreign_id": self.foreign_id,
            "foreign_status": self.foreign_status,
            "foreign_created": self.foreign_created,
            "result": self.result,
            "inserted": self.inserted,
            "updated": self.updated,
            "state": self.state.name if self.state else None
        })


class ApplicationState(Base):
    __tablename__ = "applications_states"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    application = relationship('Application', back_populates="state")
