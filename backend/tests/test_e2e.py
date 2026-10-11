import pytest
import os
from app.api.repository import run_repository_indexing
from app.models.repository import Repository

@pytest.mark.asyncio
async def test_full_application_e2e_flow(client, test_db):
    # 1. Register user
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "e2e_engineer@codepilot.ai",
        "password": "SecurePassword123!",
        "name": "E2E Test Engineer"
    })
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get workspaces
    ws_resp = await client.get("/api/v1/workspaces", headers=headers)
    assert ws_resp.status_code == 200
    workspaces = ws_resp.json()
    assert len(workspaces) > 0
    ws_id = workspaces[0]["id"]

    # 3. Create repository
    repo_resp = await client.post("/api/v1/repositories", json={
        "workspace_id": ws_id,
        "name": "Demo E2E Repo",
        "github_url": "https://github.com/example/demo",
        "default_branch": "main"
    }, headers=headers)
    assert repo_resp.status_code == 200
    repo_id = repo_resp.json()["id"]

    # 4. Trigger indexing synchronously on demo-repository
    demo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../demo-repository"))

    class TestSessionFactory:
        def __call__(self):
            class AsyncContext:
                async def __aenter__(self):
                    return test_db
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContext()

    await run_repository_indexing(repo_id, demo_dir, TestSessionFactory())

    # Verify repository files indexed
    files_resp = await client.get(f"/api/v1/repositories/{repo_id}/files", headers=headers)
    assert files_resp.status_code == 200
    files = files_resp.json()
    assert len(files) > 0

    # 5. RAG Repository Chat
    chat_resp = await client.post(f"/api/v1/repositories/{repo_id}/chat", json={
        "message": "Where is authentication implemented?"
    }, headers=headers)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert "citations" in chat_data

    # 6. Agent Execution
    agent_resp = await client.post(f"/api/v1/repositories/{repo_id}/agent", json={
        "message": "Find duplicate order creation issues."
    }, headers=headers)
    assert agent_resp.status_code == 200
    agent_data = agent_resp.json()
    assert len(agent_data["steps_taken"]) > 0

    # 7. Bug Analysis
    bug_resp = await client.post(f"/api/v1/repositories/{repo_id}/bug-analysis", json={
        "error_message": "Duplicate order creation in order_routes.py",
        "stack_trace": "Line 28 in create_order: if x_idempotency_key in PROCESSED_KEYS"
    }, headers=headers)
    assert bug_resp.status_code == 200
    bug_data = bug_resp.json()
    assert bug_data["proposed_patch"] is not None

    # 8. Code Review
    review_resp = await client.post(f"/api/v1/repositories/{repo_id}/code-review", json={
        "git_diff": "--- a/auth_routes.py\n+++ b/auth_routes.py\n@@ -22 +22 @@\n- check_auth()"
    }, headers=headers)
    assert review_resp.status_code == 200
    assert len(review_resp.json()["findings"]) > 0

    # 9. Test Generation
    test_gen_resp = await client.post(f"/api/v1/repositories/{repo_id}/generate-tests", json={
        "file_path": "backend/routes/order_routes.py",
        "framework": "pytest"
    }, headers=headers)
    assert test_gen_resp.status_code == 200
    assert "test_code" in test_gen_resp.json()

    # 10. Evaluation Run
    eval_resp = await client.post(f"/api/v1/evaluations/run/{repo_id}", headers=headers)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["total_questions"] == 5

    # 11. Observability Runs
    runs_resp = await client.get("/api/v1/ai-runs", headers=headers)
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) > 0
