import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapter.database.base import Base, TimestampMixin


class PhotoCategory(TimestampMixin, Base):
    __tablename__ = "photo_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    seo_title: Mapped[str | None] = mapped_column(String(160))
    seo_description: Mapped[str | None] = mapped_column(String(320))


class ProcessingStatus(enum.StrEnum):
    awaiting_upload = "awaiting_upload"
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Photo(TimestampMixin, Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    alt_text: Mapped[str] = mapped_column(String(400), default="")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("photo_categories.id", ondelete="SET NULL"), index=True
    )
    shot_on: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String(200))
    technical_caption: Mapped[str | None] = mapped_column(String(200))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    aspect_ratio: Mapped[float | None] = mapped_column(Numeric(8, 5, asdecimal=False))
    placeholder: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="photo_processing_status"),
        default=ProcessingStatus.awaiting_upload,
    )
    processing_error: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    # Ключ приватного оригинала в S3. Никогда не отдаётся публичным клиентам.
    original_key: Mapped[str | None] = mapped_column(String(400))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category: Mapped[PhotoCategory | None] = relationship(lazy="joined")
    variants: Mapped[list["PhotoVariant"]] = relationship(
        back_populates="photo",
        cascade="all, delete-orphan",
        order_by="PhotoVariant.width",
        lazy="selectin",
    )


class PhotoVariant(Base):
    __tablename__ = "photo_variants"
    __table_args__ = (UniqueConstraint("photo_id", "format", "width"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id", ondelete="CASCADE"))
    format: Mapped[str] = mapped_column(String(10))  # avif | webp | jpeg
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    object_key: Mapped[str] = mapped_column(String(400), unique=True)

    photo: Mapped[Photo] = relationship(back_populates="variants")
