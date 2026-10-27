import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5433/photo_test"
)
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("APP_SECRET", "test-secret")

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.core.db import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(Config("alembic.ini"), "head")
    yield


@pytest.fixture(autouse=True)
def _clean_db():
    with engine.begin() as conn:
        tables = conn.execute(
            text(
                "SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalar()
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        seed(db)
    yield


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def client():
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def lead_payload():
    return {
        "name": "Анна",
        "contact": "@anna_photo",
        "service": "personal",
        "message": "Хочу портрет на закате",
        "consent": True,
        "elapsed_ms": 15000,
        "attribution": {"landing_page": "/", "utm_source": "telegram"},
    }
