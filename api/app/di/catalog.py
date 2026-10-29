from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapter.database.base import get_db
from app.adapter.database.catalog import SQLAlchemyPublicCatalog
from app.core.config import get_settings
from app.port.catalog import PublicCatalog


def get_public_catalog(db: Session = Depends(get_db)) -> PublicCatalog:
    return SQLAlchemyPublicCatalog(db, get_settings().media_public_base_url)
