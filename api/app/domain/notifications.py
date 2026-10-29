from dataclasses import dataclass


class TemporaryError(Exception):
    """Ошибка доставки, для которой допустима повторная попытка."""


class PermanentError(Exception):
    """Задание не может быть выполнено."""


@dataclass(frozen=True, slots=True)
class LeadMessage:
    public_number: str
    name: str
    contact: str
    service: str | None
    message: str
    admin_url: str
