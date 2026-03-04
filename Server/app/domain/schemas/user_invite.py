import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.schemas.common import PaginatedResponse


class UserInviteCreate(BaseModel):
    email: EmailStr


class UserInviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: uuid.UUID
    email: EmailStr
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime


class PublicUserInviteResponse(BaseModel):
    expires_at: datetime


class PublicUserInviteConsume(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=8)


class UserInviteListResponse(PaginatedResponse[UserInviteResponse]):
    pass
