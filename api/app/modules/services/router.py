from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.services.models import Service
from app.modules.services.schemas import ServiceList, ServicePublic

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=ServiceList)
def list_services(db: Session = Depends(get_db)) -> ServiceList:
    rows = db.scalars(
        select(Service).where(Service.is_active).order_by(Service.sort_order, Service.title)
    ).all()
    return ServiceList(items=[ServicePublic.model_validate(r) for r in rows])
