import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user_invite import UserInvite


@pytest.mark.asyncio
async def test_create_user_invite_requires_auth(anon_client: AsyncClient):
    response = await anon_client.post(
        "/api/user-invites",
        json={"email": "invitee@example.com"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_user_invite_success(client: AsyncClient):
    response = await client.post(
        "/api/user-invites",
        json={"email": "invitee@example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "invitee@example.com"
    assert data["used_at"] is None
    assert "token" in data


@pytest.mark.asyncio
async def test_list_active_user_invites(client: AsyncClient):
    create_one = await client.post(
        "/api/user-invites",
        json={"email": "active1@example.com"},
    )
    assert create_one.status_code == 201

    create_two = await client.post(
        "/api/user-invites",
        json={"email": "active2@example.com"},
    )
    assert create_two.status_code == 201

    list_response = await client.get("/api/user-invites")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert {item["email"] for item in data["items"]} == {
        "active1@example.com",
        "active2@example.com",
    }


@pytest.mark.asyncio
async def test_create_user_invite_conflict_when_email_exists(
    client: AsyncClient,
):
    create_user = await client.post(
        "/api/users",
        json={
            "username": "already",
            "email": "already@example.com",
            "password": "password123",
        },
    )
    assert create_user.status_code == 201

    response = await client.post(
        "/api/user-invites",
        json={"email": "already@example.com"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_public_get_and_consume_invite(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    create_invite = await client.post(
        "/api/user-invites",
        json={"email": "invitee@example.com"},
    )
    token = create_invite.json()["token"]

    get_response = await anon_client.get(f"/api/user-invites/{token}")
    assert get_response.status_code == 200
    assert "email" not in get_response.json()

    consume_response = await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "invitee@example.com",
            "username": "invited",
            "password": "password123",
        },
    )
    assert consume_response.status_code == 204

    login_response = await anon_client.post(
        "/api/auth/login",
        json={"username": "invited", "password": "password123"},
    )
    assert login_response.status_code == 200

    second_use = await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "invitee@example.com",
            "username": "invited2",
            "password": "password123",
        },
    )
    assert second_use.status_code == 404


@pytest.mark.asyncio
async def test_new_invite_revokes_previous_for_same_email(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    first = await client.post(
        "/api/user-invites",
        json={"email": "same@example.com"},
    )
    second = await client.post(
        "/api/user-invites",
        json={"email": "same@example.com"},
    )
    first_token = first.json()["token"]
    second_token = second.json()["token"]

    old_response = await anon_client.get(f"/api/user-invites/{first_token}")
    assert old_response.status_code == 404

    new_response = await anon_client.get(f"/api/user-invites/{second_token}")
    assert new_response.status_code == 200


@pytest.mark.asyncio
async def test_expired_invite_returns_404(
    client: AsyncClient,
    anon_client: AsyncClient,
    session: AsyncSession,
):
    create_invite = await client.post(
        "/api/user-invites",
        json={"email": "expires@example.com"},
    )
    token = create_invite.json()["token"]

    invite = (
        await session.execute(
            select(UserInvite).where(UserInvite.token == uuid.UUID(token))
        )
    ).scalar_one()
    invite.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await session.flush()

    response = await anon_client.get(f"/api/user-invites/{token}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_returns_only_active_invites(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    first = await client.post(
        "/api/user-invites",
        json={"email": "filtered@example.com"},
    )
    token = first.json()["token"]

    await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "filtered@example.com",
            "username": "filtereduser",
            "password": "password123",
        },
    )

    list_response = await client.get("/api/user-invites")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_consume_invite_with_wrong_email_returns_400(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    create_invite = await client.post(
        "/api/user-invites",
        json={"email": "correct@example.com"},
    )
    token = create_invite.json()["token"]

    response = await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "wrong@example.com",
            "username": "invitedx",
            "password": "password123",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_consume_invite_rejects_username_with_space(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    create_invite = await client.post(
        "/api/user-invites",
        json={"email": "spaceusername@example.com"},
    )
    token = create_invite.json()["token"]

    response = await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "spaceusername@example.com",
            "username": "invalid user",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "Username" in response.json()["detail"]


@pytest.mark.asyncio
async def test_consume_invite_rejects_case_insensitive_duplicate_username(
    client: AsyncClient,
    anon_client: AsyncClient,
):
    create_user = await client.post(
        "/api/users",
        json={
            "username": "ExistingUser",
            "email": "existing-user@example.com",
            "password": "password123",
        },
    )
    assert create_user.status_code == 201

    create_invite = await client.post(
        "/api/user-invites",
        json={"email": "newinvite@example.com"},
    )
    token = create_invite.json()["token"]

    response = await anon_client.post(
        f"/api/user-invites/{token}",
        json={
            "email": "newinvite@example.com",
            "username": "existinguser",
            "password": "password123",
        },
    )
    assert response.status_code == 409
