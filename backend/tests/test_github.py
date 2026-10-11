import pytest

@pytest.mark.asyncio
async def test_list_github_repositories(client):
    response = await client.get("/api/v1/github/repositories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]

@pytest.mark.asyncio
async def test_get_github_pull_requests(client):
    response = await client.get("/api/v1/github/repositories/owner/repo/pulls")
    assert response.status_code == 200
    prs = response.json()
    assert len(prs) > 0
    assert prs[0]["number"] == 42
