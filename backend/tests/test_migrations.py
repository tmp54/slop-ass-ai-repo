from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


def test_migration_creates_all_tables(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        get_settings.cache_clear()
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"handoffs", "brief_versions", "transitions", "restatements", "questions", "confirmations"} <= tables
