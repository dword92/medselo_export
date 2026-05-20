from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.core.config import settings


# Для SQLite включаем поддержку внешних ключей
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно только для SQLite
    echo=settings.DEBUG,
)

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency для FastAPI — выдаёт сессию и закрывает после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
