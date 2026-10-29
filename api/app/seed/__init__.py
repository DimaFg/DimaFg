"""Начальные данные (категории и услуги из прототипа). Повторный запуск безопасен."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapter.database.models.portfolio import PhotoCategory
from app.adapter.database.models.services import Service

DATA = Path(__file__).with_name("data.json")


def seed(db: Session) -> dict[str, int]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    created = {"categories": 0, "services": 0}
    for item in data["categories"]:
        if not db.scalars(select(PhotoCategory).where(PhotoCategory.slug == item["slug"])).first():
            db.add(PhotoCategory(**item))
            created["categories"] += 1
    for item in data["services"]:
        if not db.scalars(select(Service).where(Service.slug == item["slug"])).first():
            db.add(Service(**item))
            created["services"] += 1
    db.commit()
    return created
