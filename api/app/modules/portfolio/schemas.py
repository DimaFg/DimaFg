from datetime import date
from typing import Literal

from app.core.schemas import ApiModel


class CategoryPublic(ApiModel):
    slug: str
    title: str
    description: str


class ImageSource(ApiModel):
    format: Literal["avif", "webp", "jpeg"]
    width: int
    height: int
    url: str


class PhotoPublic(ApiModel):
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
    sources: list[ImageSource]


class PortfolioList(ApiModel):
    categories: list[CategoryPublic]
    items: list[PhotoPublic]
