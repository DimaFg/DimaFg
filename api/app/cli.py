"""Служебные команды.

python -m app.cli create-admin --email owner@example.com   # пароль спросит интерактивно
python -m app.cli set-password --email owner@example.com
python -m app.cli seed
python -m app.cli worker
python -m app.cli openapi > openapi.json
"""

import argparse
import getpass
import json
import os
import sys

from sqlalchemy import select

import app.models  # noqa: F401 — регистрирует все модели (внешние ключи между модулями)
from app.core.logging import configure_logging

MIN_PASSWORD_LENGTH = 12


def _read_password() -> str:
    # ADMIN_PASSWORD допускается для неинтерактивного развёртывания; в историю shell не попадает.
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Пароль: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов.")
    if not os.environ.get("ADMIN_PASSWORD") and password != getpass.getpass("Повторите: "):
        sys.exit("Пароли не совпадают.")
    return password


def cmd_create_admin(args) -> None:
    from app.core.db import SessionLocal
    from app.modules.auth.models import Admin
    from app.modules.auth.passwords import hash_password

    email = args.email.strip().lower()
    with SessionLocal() as db:
        if db.scalars(select(Admin).where(Admin.email == email)).first():
            sys.exit("Администратор с таким email уже существует.")
        db.add(Admin(email=email, password_hash=hash_password(_read_password())))
        db.commit()
    print(f"Администратор {email} создан.")


def cmd_set_password(args) -> None:
    from app.core.db import SessionLocal
    from app.modules.auth.models import Admin, AdminSession
    from app.modules.auth.passwords import hash_password

    email = args.email.strip().lower()
    with SessionLocal() as db:
        admin = db.scalars(select(Admin).where(Admin.email == email)).first()
        if admin is None:
            sys.exit("Администратор не найден.")
        admin.password_hash = hash_password(_read_password())
        # Смена пароля завершает все активные сессии.
        for s in db.scalars(select(AdminSession).where(AdminSession.admin_id == admin.id)):
            db.delete(s)
        db.commit()
    print("Пароль обновлён, активные сессии завершены.")


def cmd_seed(_args) -> None:
    from app.core.db import SessionLocal
    from app.seed import seed

    with SessionLocal() as db:
        print(json.dumps(seed(db), ensure_ascii=False))


def cmd_worker(_args) -> None:
    from app.core.db import SessionLocal
    from app.modules.notifications.worker import run_forever

    configure_logging()
    run_forever(SessionLocal)


def cmd_openapi(_args) -> None:
    from app.main import create_app

    print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin")
    p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_create_admin)
    p = sub.add_parser("set-password")
    p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_set_password)
    sub.add_parser("seed").set_defaults(func=cmd_seed)
    sub.add_parser("worker").set_defaults(func=cmd_worker)
    sub.add_parser("openapi").set_defaults(func=cmd_openapi)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
