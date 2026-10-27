import subprocess
import sys


def test_app_import_registers_all_models():
    """Регрессия: без импорта app.models flush падал с NoReferencedTableError (admins).

    Проверяется в отдельном процессе, потому что в тестах модели уже загружены через Alembic.
    """
    code = (
        "import app.main\n"
        "from sqlalchemy.orm import configure_mappers\n"
        "from app.core.db import Base\n"
        "configure_mappers()\n"
        "for t in Base.metadata.sorted_tables:\n"
        "    for fk in t.foreign_keys:\n"
        "        fk.column\n"
        "print(len(Base.metadata.tables))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd="."
    )
    assert int(out.stdout.strip()) == 10
