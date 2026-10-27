import uuid

from app.core.schemas import ApiModel


class ServicePublic(ApiModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    description: str
    price_text: str
    duration_text: str
    sort_order: int
    seo_title: str | None
    seo_description: str | None


class ServiceList(ApiModel):
    items: list[ServicePublic]
