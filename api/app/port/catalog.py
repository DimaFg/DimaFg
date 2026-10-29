from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ServiceView:
    id: UUID
    slug: str
    title: str
    summary: str
    description: str
    price_text: str
    duration_text: str
    sort_order: int
    seo_title: str | None
    seo_description: str | None


@dataclass(frozen=True, slots=True)
class CategoryView:
    slug: str
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class ImageSourceView:
    format: str
    width: int
    height: int
    url: str


@dataclass(frozen=True, slots=True)
class PhotoView:
    slug: str
    title: str
    description: str
    alt_text: str
    category: str | None
    shot_on: date | None
    location: str | None
    technical_caption: str | None
    width: int | None
    height: int | None
    aspect_ratio: float | None
    placeholder: str | None
    is_featured: bool
    sources: list[ImageSourceView]


@dataclass(frozen=True, slots=True)
class PortfolioView:
    categories: list[CategoryView]
    items: list[PhotoView]


class PublicCatalog(Protocol):
    def list_services(self) -> list[ServiceView]: ...

    def list_portfolio(self, category: str | None, featured: bool | None) -> PortfolioView: ...

    def get_photo(self, slug: str) -> PhotoView | None: ...
