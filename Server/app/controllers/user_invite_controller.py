import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.user_invite.consume_user_invite import ConsumeUserInvite
from app.application.user_invite.create_user_invite import CreateUserInvite
from app.application.user_invite.get_user_invite import GetUserInvite
from app.application.user_invite.list_user_invites import ListUserInvites
from app.controllers.dependencies import (
    user_invite_builder,
    user_invite_consume_builder,
    user_invite_create_builder,
)
from app.domain.exceptions import ConflictError
from app.domain.schemas.user_invite import (
    PublicUserInviteConsume,
    PublicUserInviteResponse,
    UserInviteCreate,
    UserInviteListResponse,
    UserInviteResponse,
)

public_router = APIRouter(tags=["User Invites"])
router = APIRouter(tags=["User Invites"])


@router.post(
    "/user-invites",
    response_model=UserInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_invite(
    data: UserInviteCreate,
    create_use_case: CreateUserInvite = Depends(
        user_invite_create_builder(CreateUserInvite)
    ),
):
    try:
        invite = await create_use_case.execute(data.email)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return UserInviteResponse.model_validate(invite)


@router.get(
    "/user-invites",
    response_model=UserInviteListResponse,
)
async def list_user_invites(
    list_use_case: ListUserInvites = Depends(user_invite_builder(ListUserInvites)),
):
    items, total = await list_use_case.execute()
    return UserInviteListResponse(
        items=[UserInviteResponse.model_validate(i) for i in items],
        total=total,
    )


@public_router.get(
    "/user-invites/{token}",
    response_model=PublicUserInviteResponse,
)
async def get_user_invite(
    token: uuid.UUID,
    get_use_case: GetUserInvite = Depends(user_invite_builder(GetUserInvite)),
):
    invite = await get_use_case.execute(token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )

    return PublicUserInviteResponse(
        expires_at=invite.expires_at,
    )


@public_router.post(
    "/user-invites/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def consume_user_invite(
    token: uuid.UUID,
    data: PublicUserInviteConsume,
    consume_use_case: ConsumeUserInvite = Depends(
        user_invite_consume_builder(ConsumeUserInvite)
    ),
):
    try:
        user = await consume_use_case.execute(
            token,
            data.email,
            data.username,
            data.password,
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token invalido ou expirado",
        )
