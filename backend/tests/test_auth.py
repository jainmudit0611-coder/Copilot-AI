import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    # Test Register
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "testuser@codepilot.ai",
        "password": "Password123!",
        "name": "Test Engineer"
    })
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@codepilot.ai"

    # Test Login with correct credentials
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "testuser@codepilot.ai",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

@pytest.mark.asyncio
async def test_demo_user_login_and_auth_flow(client):
    # Ensure demo user is seeded by triggering get_current_user fallback
    me_fallback = await client.get("/api/v1/auth/me")
    assert me_fallback.status_code == 200
    assert me_fallback.json()["email"] == "developer@codepilot.ai"

    # Test Login as seeded demo user with valid default password
    demo_login = await client.post("/api/v1/auth/login", json={
        "email": "developer@codepilot.ai",
        "password": "Password123!"
    })
    assert demo_login.status_code == 200
    token_data = demo_login.json()
    assert "access_token" in token_data
    assert token_data["user"]["email"] == "developer@codepilot.ai"

    # Test authenticated /me endpoint using token
    token = token_data["access_token"]
    me_auth = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_auth.status_code == 200
    assert me_auth.json()["email"] == "developer@codepilot.ai"

@pytest.mark.asyncio
async def test_login_invalid_password(client):
    # Trigger demo user seeding
    await client.get("/api/v1/auth/me")

    # Attempt login with incorrect password
    bad_login = await client.post("/api/v1/auth/login", json={
        "email": "developer@codepilot.ai",
        "password": "WrongPassword999!"
    })
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@codepilot.ai",
        "password": "Password123!"
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]
