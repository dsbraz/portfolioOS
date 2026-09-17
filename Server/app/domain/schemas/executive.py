import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

from app.domain.schemas.common import PaginatedResponse

_PHONE_SEPARATORS = re.compile(r"[\s().\-/]")


def _normalize_phone(value: object) -> object:
    if not isinstance(value, str):
        return value
    return _PHONE_SEPARATORS.sub("", value) or None


def _normalize_email(value: object) -> object:
    if not isinstance(value, str):
        return value
    return value.strip().lower() or None


# E.164 with the country code required: the fund's executives are not all in
# Brazil, and a local-format number cannot be told apart from a foreign one.
_E164 = Annotated[str, StringConstraints(pattern=r"^\+[0-9]{8,15}$")]
InternationalPhone = Annotated[_E164 | None, BeforeValidator(_normalize_phone)]
ContactEmail = Annotated[EmailStr | None, BeforeValidator(_normalize_email)]


class ExecutiveBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str | None = Field(None, max_length=255)
    linkedin: str | None = Field(None, max_length=512)


class ExecutiveCreate(ExecutiveBase):
    email: ContactEmail = None
    phone: InternationalPhone = None


class ExecutiveUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, max_length=255)
    email: ContactEmail = None
    phone: InternationalPhone = None
    linkedin: str | None = Field(None, max_length=512)


class ExecutiveResponse(ExecutiveBase):
    model_config = ConfigDict(from_attributes=True)

    # Plain strings: records saved before the contact rules must still load.
    email: str | None = None
    phone: str | None = None
    id: uuid.UUID
    startup_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ExecutiveListResponse(PaginatedResponse[ExecutiveResponse]):
    pass
