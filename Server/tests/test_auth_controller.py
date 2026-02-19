import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(anon_client: AsyncClient, client: AsyncClient):
    user_payload = {
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": "securepass123",
    }
    create_resp = await client.post("/api/users", json=user_payload)
    assert create_resp.status_code == 201

    login_resp = await anon_client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "securepass123"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(anon_client: AsyncClient):
    response = await anon_client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais invalidas"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
    }
    response = await client.post("/api/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    payload = {
        "username": "dupuser",
        "email": "dup1@example.com",
        "password": "password123",
    }
    resp1 = await client.post("/api/users", json=payload)
    assert resp1.status_code == 201

    payload["email"] = "dup2@example.com"
    resp2 = await client.post("/api/users", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload1 = {
        "username": "emailuser1",
        "email": "same@example.com",
        "password": "password123",
    }
    resp1 = await client.post("/api/users", json=payload1)
    assert resp1.status_code == 201

    payload2 = {
        "username": "emailuser2",
        "email": "same@example.com",
        "password": "password123",
    }
    resp2 = await client.post("/api/users", json=payload2)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    payload = {
        "username": "shortpw",
        "email": "short@example.com",
        "password": "1234567",
    }
    response = await client.post("/api/users", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protected_route_without_token(anon_client: AsyncClient):
    response = await anon_client.get("/api/startups")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient):
    response = await client.get("/api/startups")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(anon_client: AsyncClient):
    response = await anon_client.get(
        "/api/startups",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_public_route_health_no_token(anon_client: AsyncClient):
    response = await anon_client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_register_requires_auth(anon_client: AsyncClient):
    payload = {
        "username": "unauth",
        "email": "unauth@example.com",
        "password": "password123",
    }
    response = await anon_client.post("/api/users", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    create_resp = await client.post(
        "/api/users",
        json={
            "username": "editme",
            "email": "editme@example.com",
            "password": "password123",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/users/{user_id}",
        json={"username": "edited", "email": "edited@example.com"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["username"] == "edited"
    assert data["email"] == "edited@example.com"


@pytest.mark.asyncio
async def test_update_user_password(client: AsyncClient, anon_client: AsyncClient):
    create_resp = await client.post(
        "/api/users",
        json={
            "username": "pwdchange",
            "email": "pwdchange@example.com",
            "password": "oldpass123",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/users/{user_id}",
        json={"password": "newpass123"},
    )
    assert update_resp.status_code == 200

    login_resp = await anon_client.post(
        "/api/auth/login",
        json={"username": "pwdchange", "password": "newpass123"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_deactivate_other_user(client: AsyncClient):
    create_resp = await client.post(
        "/api/users",
        json={
            "username": "todeactivate",
            "email": "deact@example.com",
            "password": "password123",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/users/{user_id}",
        json={"is_active": False},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_cannot_deactivate_self(client: AsyncClient):
    # The client fixture's user is "testadmin" — get their id
    users_resp = await client.get("/api/users")
    current_user = next(
        u for u in users_resp.json()["items"] if u["username"] == "testadmin"
    )

    update_resp = await client.patch(
        f"/api/users/{current_user['id']}",
        json={"is_active": False},
    )
    assert update_resp.status_code == 400
    assert "proprio" in update_resp.json()["detail"]
