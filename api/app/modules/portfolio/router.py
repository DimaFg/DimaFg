from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.modules.portfolio.models import Photo, PhotoCategory, ProcessingStatus
from app.modules.portfolio.schemas import CategoryPublic, ImageSource, PhotoPublic, PortfolioList

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def _public_photos():
    return select(Photo).where(
        Photo.is_published,
        Photo.archived_at.is_(None),
        Photo.processing_status == ProcessingStatus.ready,
    )


def to_public(photo: Photo) -> PhotoPublic:
    base = get_settings().media_public_base_url.rstrip("/")
    return PhotoPublic(
        slug=photo.slug,
        title=photo.title,
        description=photo.description,
        alt_text=photo.alt_text,
        category=photo.category.slug if photo.category else None,
        shot_on=photo.shot_on,
        location=photo.location,
        technical_caption=photo.technical_caption,
        width=photo.width,
        height=photo.height,
        aspect_ratio=photo.aspect_ratio,
        placeholder=photo.placeholder,
        is_featured=photo.is_featured,
        sources=[
            ImageSource(
                format=v.format, width=v.width, height=v.height, url=f"{base}/{v.object_key}"
            )
            for v in photo.variants
        ],
    )


@router.get("", response_model=PortfolioList)
def list_portfolio(
    db: Session = Depends(get_db),
    category: Annotated[str | None, Query(max_length=80, pattern=SLUG_PATTERN)] = None,
    featured: bool | None = None,
) -> PortfolioList:
    categories = db.scalars(
        select(PhotoCategory)
        .where(PhotoCategory.is_active)
        .order_by(PhotoCategory.sort_order, PhotoCategory.title)
    ).all()

    query = _public_photos()
    if category:
        query = query.join(Photo.category).where(PhotoCategory.slug == category)
    if featured is not None:
        query = query.where(Photo.is_featured == featured)
    photos = db.scalars(query.order_by(Photo.sort_order, Photo.published_at.desc())).unique().all()

    return PortfolioList(
        categories=[CategoryPublic.model_validate(c) for c in categories],
        items=[to_public(p) for p in photos],
    )


@router.get("/{slug}", response_model=PhotoPublic)
def get_photo(
    slug: Annotated[str, Path(max_length=120, pattern=SLUG_PATTERN)],
    db: Session = Depends(get_db),
) -> PhotoPublic:
    photo = db.scalars(_public_photos().where(Photo.slug == slug)).unique().first()
    if photo is None:
        raise ApiError(404, "not_found", "Фотография не найдена.")
    return to_public(photo)
