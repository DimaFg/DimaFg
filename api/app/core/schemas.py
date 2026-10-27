from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrictInput(BaseModel):
    """Входные модели не принимают неизвестных полей."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
