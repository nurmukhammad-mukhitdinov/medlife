from typing import Any, Dict, List

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

DeclarativeBase = declarative_base()


class SQLModel(DeclarativeBase):
    __abstract__ = True
    created_at = Column(DateTime, default=func.now(), nullable=False)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def schema(cls) -> str:
        _schema = cls.__mapper__.selectable.schema
        if _schema is None:
            raise ValueError("Cannot identify model schema")
        return _schema

    @classmethod
    def table_name(cls) -> str:
        return cls.__tablename__

    @classmethod
    def fields(cls) -> List[str]:
        return cls.__mapper__.selectable.c.keys()

    def to_dict(self) -> Dict[str, Any]:
        _dict: Dict[str, Any] = dict()
        for key in self.__mapper__.c.keys():
            _dict[key] = getattr(self, key)
        return _dict
