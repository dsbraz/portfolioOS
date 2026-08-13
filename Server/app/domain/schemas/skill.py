from pydantic import BaseModel, ConfigDict

from app.domain.schemas.common import PaginatedResponse


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    version: str
    writes: bool
    reads_external: bool
    published: bool
    blocked_reason: str | None = None
    files: list[str] | None = None


class SkillListResponse(PaginatedResponse[SkillResponse]):
    pass
