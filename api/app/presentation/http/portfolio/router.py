from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.di.catalog import get_public_catalog
from app.port.catalog import PublicCatalog
from app.presentation.http.errors import ApiError
from app.presentation.http.portfolio.schemas import PhotoPublic, PortfolioList

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


@router.get("", response_model=PortfolioList)
def list_portfolio(
    catalog: PublicCatalog = Depends(get_public_catalog),
    category: Annotated[str | None, Query(max_length=80, pattern=SLUG_PATTERN)] = None,
    featured: bool | None = None,
) -> PortfolioList:
    return PortfolioList.model_validate(catalog.list_portfolio(category, featured))


@router.get("/{slug}", response_model=PhotoPublic)
def get_photo(
    slug: Annotated[str, Path(max_length=120, pattern=SLUG_PATTERN)],
    catalog: PublicCatalog = Depends(get_public_catalog),
) -> PhotoPublic:
    photo = catalog.get_photo(slug)
    if photo is None:
        raise ApiError(404, "not_found", "Фотография не найдена.")
    return PhotoPublic.model_validate(photo)
