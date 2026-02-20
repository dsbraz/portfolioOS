import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.common import PaginatedResponse


class ExecutiveBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    linkedin: str | None = Field(None, max_length=512)


class ExecutiveCreate(ExecutiveBase):
    pass

class ExecutiveUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    linkedin: str | None = Field(None, max_length=512)


class ExecutiveResponse(ExecutiveBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    startup_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ExecutiveListResponse(PaginatedResponse[ExecutiveResponse]):
    pass
