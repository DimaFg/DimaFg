from fastapi import APIRouter, Depends

from app.di.catalog import get_public_catalog
from app.port.catalog import PublicCatalog
from app.presentation.http.services.schemas import ServiceList, ServicePublic

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=ServiceList)
def list_services(catalog: PublicCatalog = Depends(get_public_catalog)) -> ServiceList:
    return ServiceList(items=[ServicePublic.model_validate(row) for row in catalog.list_services()])
