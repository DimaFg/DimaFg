import re
from typing import Annotated

from pydantic import Field, field_validator

from app.presentation.http.schemas import ApiModel, StrictInput

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
OptionalShort = Annotated[str | None, Field(default=None, max_length=200)]
OptionalUrl = Annotated[str | None, Field(default=None, max_length=500)]


class LeadAttribution(StrictInput):
    referrer: OptionalUrl
    landing_page: OptionalUrl
    utm_source: OptionalShort
    utm_medium: OptionalShort
    utm_campaign: OptionalShort
    utm_term: OptionalShort
    utm_content: OptionalShort


class LeadCreate(StrictInput):
    name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=3, max_length=200)
    service: str | None = Field(
        default=None,
        max_length=80,
        pattern=SLUG_PATTERN,
        description="slug услуги или `other`",
    )
    message: str = Field(default="", max_length=3000)
    consent: bool = Field(description="Согласие на обработку персональных данных")
    privacy_policy_version: str | None = Field(default=None, max_length=40)
    # Honeypot: скрытое поле, которое человек не заполняет.
    website: str = Field(default="", max_length=200)
    # Сколько миллисекунд прошло между показом формы и отправкой.
    elapsed_ms: int | None = Field(default=None, ge=0, le=7 * 24 * 3600 * 1000)
    attribution: LeadAttribution | None = None

    @field_validator("name")
    @classmethod
    def _name_has_letters(cls, v: str) -> str:
        if not re.search(r"[^\W\d_]", v):
            raise ValueError("Укажите имя буквами.")
        return v

    @field_validator("consent")
    @classmethod
    def _consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Необходимо согласие на обработку персональных данных.")
        return v


class LeadCreated(ApiModel):
    public_number: str
    expected_response: str
