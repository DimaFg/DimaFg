import re

from app.modules.leads.models import ContactType

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_TELEGRAM = re.compile(r"^(?:@|(?:https?://)?t\.me/)?([A-Za-z][A-Za-z0-9_]{4,31})$")
_PHONE = re.compile(r"^\+?[\d\s().-]{7,25}$")


def classify_contact(raw: str) -> tuple[ContactType, str]:
    """Определяет тип контакта и нормализованное значение для дедупликации."""
    value = raw.strip()
    if _EMAIL.match(value):
        return ContactType.email, value.lower()
    if _PHONE.match(value):
        digits = re.sub(r"\D", "", value)
        if 10 <= len(digits) <= 15:
            if len(digits) == 11 and digits.startswith("8"):
                digits = "7" + digits[1:]
            return ContactType.phone, "+" + digits
    if m := _TELEGRAM.match(value):
        return ContactType.telegram, "@" + m.group(1).lower()
    return ContactType.other, re.sub(r"\s+", " ", value.lower())
