import pytest
from app.ingestion.scanner import RepositoryScanner
from app.ingestion.parser import CodeParser
from app.ingestion.chunker import IntelligentChunker
from app.ingestion.secret_scanner import scan_and_redact_secrets

def test_secret_scanner_redaction():
    code_with_secret = 'API_KEY = "AKIA1234567890ABCDEF"'
    redacted = scan_and_redact_secrets(code_with_secret)
    assert "[REDACTED_AWS_ACCESS_KEY]" in redacted
    assert "AKIA1234567890ABCDEF" not in redacted

def test_code_parser_symbol_extraction():
    py_code = """
def calculate_order_total(items):
    return sum(item.price for item in items)

class OrderProcessor:
    def process(self):
        pass
"""
    symbols = CodeParser.extract_symbols(py_code, "Python")
    symbol_names = [s["name"] for s in symbols]
    assert "calculate_order_total" in symbol_names
    assert "OrderProcessor" in symbol_names

def test_intelligent_chunker():
    ts_code = """export const loginUser = async (email: string) => {
  return await fetch('/api/login');
};"""
    chunks = IntelligentChunker.chunk_file("auth.ts", "TypeScript", ts_code)
    assert len(chunks) > 0
    assert chunks[0]["file_path"] == "auth.ts"

@pytest.mark.asyncio
async def test_repository_indexing_lifecycle_and_transitions(test_db):
    import os
    import tempfile
    from app.api.repository import run_repository_indexing
    from app.models.repository import Repository, IndexStatus

    repo = Repository(
        workspace_id="test-ws",
        name="Test Ingestion Repo",
        default_branch="main",
        status=IndexStatus.PENDING
    )
    test_db.add(repo)
    await test_db.commit()
    await test_db.refresh(repo)
    assert repo.status == IndexStatus.PENDING

    with tempfile.TemporaryDirectory() as tmp_dir:
        sample_file = os.path.join(tmp_dir, "auth_service.py")
        with open(sample_file, "w") as f:
            f.write("def login(email, password):\n    return True\n")

        class SessionFactory:
            def __call__(self):
                class AsyncContext:
                    async def __aenter__(self):
                        return test_db
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        pass
                return AsyncContext()

        await run_repository_indexing(repo.id, tmp_dir, SessionFactory())

    updated_repo = await test_db.get(Repository, repo.id)
    assert updated_repo.status == IndexStatus.COMPLETED
    assert updated_repo.indexed_files_count == 1
    assert updated_repo.indexed_chunks_count >= 1

@pytest.mark.asyncio
async def test_repository_indexing_invalid_repo_safe_exit(test_db):
    from app.api.repository import run_repository_indexing

    class SessionFactory:
        def __call__(self):
            class AsyncContext:
                async def __aenter__(self):
                    return test_db
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContext()

    # Should exit safely without unhandled exception
    await run_repository_indexing("nonexistent-repo-999", ".", SessionFactory())

@pytest.mark.asyncio
async def test_indexing_endpoint_not_found(client):
    resp = await client.post("/api/v1/repositories/nonexistent-uuid-12345/index")
    assert resp.status_code == 404
    assert "Repository not found" in resp.json()["detail"]
