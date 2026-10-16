from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def configure_sqlite(engine: Engine) -> None:
    """SQLite için yabancı anahtarları açar ve her transaction'ı BEGIN IMMEDIATE ile başlatır.

    BEGIN IMMEDIATE yazma kilidini en başta alır; böylece aynı anda gelen iki al-sat
    isteği bakiyeyi aynı anda okuyup ikisi de onaylanamaz (bakiye eksiye düşemez).
    """

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        dbapi_conn.isolation_level = None  # transaction'ları biz yönetiyoruz
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        conn.exec_driver_sql("BEGIN IMMEDIATE")


def make_engine(url: str, **kwargs) -> Engine:
    if url.startswith("sqlite"):
        kwargs.setdefault("connect_args", {"check_same_thread": False})
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        configure_sqlite(engine)
    return engine


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
