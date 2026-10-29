from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapter.database.models.portfolio import Photo, PhotoCategory, ProcessingStatus
from app.adapter.database.models.services import Service
from app.port.catalog import CategoryView, ImageSourceView, PhotoView, PortfolioView, ServiceView


class SQLAlchemyPublicCatalog:
    def __init__(self, session: Session, media_public_base_url: str):
        self.session = session
        self.media_base_url = media_public_base_url.rstrip("/")

    def list_services(self) -> list[ServiceView]:
        rows = self.session.scalars(
            select(Service).where(Service.is_active).order_by(Service.sort_order, Service.title)
        ).all()
        return [
            ServiceView(
                id=row.id,
                slug=row.slug,
                title=row.title,
                summary=row.summary,
                description=row.description,
                price_text=row.price_text,
                duration_text=row.duration_text,
                sort_order=row.sort_order,
                seo_title=row.seo_title,
                seo_description=row.seo_description,
            )
            for row in rows
        ]

    @staticmethod
    def _public_photos():
        return select(Photo).where(
            Photo.is_published,
            Photo.archived_at.is_(None),
            Photo.processing_status == ProcessingStatus.ready,
        )

    def _photo_view(self, photo: Photo) -> PhotoView:
        return PhotoView(
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
                ImageSourceView(
                    format=v.format,
                    width=v.width,
                    height=v.height,
                    url=f"{self.media_base_url}/{v.object_key}",
                )
                for v in photo.variants
            ],
        )

    def list_portfolio(self, category: str | None, featured: bool | None) -> PortfolioView:
        categories = self.session.scalars(
            select(PhotoCategory)
            .where(PhotoCategory.is_active)
            .order_by(PhotoCategory.sort_order, PhotoCategory.title)
        ).all()
        query = self._public_photos()
        if category:
            query = query.join(Photo.category).where(PhotoCategory.slug == category)
        if featured is not None:
            query = query.where(Photo.is_featured == featured)
        photos = (
            self.session.scalars(query.order_by(Photo.sort_order, Photo.published_at.desc()))
            .unique()
            .all()
        )
        return PortfolioView(
            categories=[CategoryView(c.slug, c.title, c.description) for c in categories],
            items=[self._photo_view(photo) for photo in photos],
        )

    def get_photo(self, slug: str) -> PhotoView | None:
        photo = (
            self.session.scalars(self._public_photos().where(Photo.slug == slug)).unique().first()
        )
        return self._photo_view(photo) if photo else None
