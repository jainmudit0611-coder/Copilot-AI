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


@pytest.mark.asyncio
async def test_workspace_and_repository_authorization(client):
    """Verify authorization checks for repositories, workspaces, and job polling."""
    # 1. Register User A
    user_a_reg = await client.post("/api/v1/auth/register", json={
        "email": "owner_a@codepilot.ai",
        "password": "Password123!",
        "name": "Owner A"
    })
    token_a = user_a_reg.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A creates Workspace A
    ws_resp = await client.post("/api/v1/workspaces", json={
        "name": "Workspace A",
        "slug": "ws-a-unique"
    }, headers=headers_a)
    ws_id = ws_resp.json()["id"]

    # User A creates Repository A
    repo_resp = await client.post("/api/v1/repositories", json={
        "workspace_id": ws_id,
        "name": "Repo A",
        "github_url": "https://github.com/example/repo-a",
        "default_branch": "main"
    }, headers=headers_a)
    repo_id = repo_resp.json()["id"]

    # 2. Register User B (different user, not in workspace A)
    user_b_reg = await client.post("/api/v1/auth/register", json={
        "email": "attacker_b@codepilot.ai",
        "password": "Password123!",
        "name": "Attacker B"
    })
    token_b = user_b_reg.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B tries to attach a repo to User A's workspace -> 403 Forbidden
    unauthorized_create = await client.post("/api/v1/repositories", json={
        "workspace_id": ws_id,
        "name": "Intruder Repo",
        "github_url": "https://github.com/example/intruder",
        "default_branch": "main"
    }, headers=headers_b)
    assert unauthorized_create.status_code == 403

    # 4. User B tries to trigger indexing on User A's repo -> 403 Forbidden
    unauthorized_index = await client.post(f"/api/v1/repositories/{repo_id}/index", headers=headers_b)
    assert unauthorized_index.status_code == 403

    # 5. User B tries to poll job status on User A's repo -> 403 Forbidden
    unauthorized_job_poll = await client.get(f"/api/v1/repositories/{repo_id}/jobs/job_123", headers=headers_b)
    assert unauthorized_job_poll.status_code == 403

    # 6. User B tries to list files on User A's repo -> 403 Forbidden
    unauthorized_files = await client.get(f"/api/v1/repositories/{repo_id}/files", headers=headers_b)
    assert unauthorized_files.status_code == 403

    # 7. User B tries to chat with User A's repo -> 403 Forbidden
    unauthorized_chat = await client.post(f"/api/v1/repositories/{repo_id}/chat", json={
        "message": "Reveal secrets"
    }, headers=headers_b)
    assert unauthorized_chat.status_code == 403

    # 8. User A accesses their own repo -> Success (200)
    authorized_files = await client.get(f"/api/v1/repositories/{repo_id}/files", headers=headers_a)
    assert authorized_files.status_code == 200

    # Polling nonexistent repo returns 404
    not_found_poll = await client.get("/api/v1/repositories/nonexistent_repo/jobs/job_123", headers=headers_a)
    assert not_found_poll.status_code == 404
