from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@lru_cache
def expected_revision() -> str | None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    return ScriptDirectory.from_config(config).get_current_head()


def check_database(engine: Engine) -> str:
    """БД доступна и схема соответствует коду. Иначе — RuntimeError.

    Ловит выкладку, в которой новая версия приложения запущена без применённых миграций.
    """
    with engine.connect() as conn:
        revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
    expected = expected_revision()
    if revision != expected:
        raise RuntimeError(f"database revision mismatch: current={revision} expected={expected}")
    return revision
