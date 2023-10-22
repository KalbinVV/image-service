import enum

from sqlalchemy import create_engine, Column, Text, Enum, Date, Integer
from sqlalchemy.orm import declarative_base

import config

Engine = create_engine(config.DB_URL)

Base = declarative_base()


class StatusEnum(enum.StrEnum):
    processing = 'processing'
    completed = 'completed'
    cancelled = 'cancelled'


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    result_file_path = Column(Text)
    loaded_at = Column(Date, nullable=False)

    status = Column(Enum(StatusEnum), nullable=False)


def init_tables() -> None:
    Base.metadata.create_all(bind=Engine)
