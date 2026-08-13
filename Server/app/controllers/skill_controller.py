from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.application.skill.get_skill_pack import GetSkillPack
from app.application.skill.get_skill_package import GetSkillPackage
from app.application.skill.list_skills import ListSkills
from app.controllers.dependencies import skill_builder, skills_access
from app.domain.schemas.skill import SkillListResponse, SkillResponse

public_router = APIRouter(tags=["Skills"])

ZIP_BINARY_RESPONSE = {
    "application/zip": {
        "schema": {
            "type": "string",
            "format": "binary",
        }
    }
}


@public_router.get(
    "/skills",
    response_model=SkillListResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(skills_access)],
)
async def list_skills(
    use_case: ListSkills = Depends(skill_builder(ListSkills)),
):
    items, total = await use_case.execute()
    return SkillListResponse(
        items=[SkillResponse.model_validate(item) for item in items],
        total=total,
    )


@public_router.get(
    "/skills.zip",
    dependencies=[Depends(skills_access)],
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "description": "Downloadable complete skill pack.",
            "content": ZIP_BINARY_RESPONSE,
        }
    },
)
async def download_skill_pack(
    use_case: GetSkillPack = Depends(skill_builder(GetSkillPack)),
) -> Response:
    package = await use_case.execute()
    return Response(
        content=package,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="portfolioos.zip"',
        },
    )


@public_router.get(
    "/skills/{name}.zip",
    dependencies=[Depends(skills_access)],
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "description": "Downloadable skill package.",
            "content": ZIP_BINARY_RESPONSE,
        }
    },
)
async def download_skill(
    name: str,
    use_case: GetSkillPackage = Depends(skill_builder(GetSkillPackage)),
) -> Response:
    package = await use_case.execute(name)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill nao encontrada",
        )

    return Response(
        content=package,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{name}.zip"',
        },
    )
