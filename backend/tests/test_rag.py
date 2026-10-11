import pytest
from app.rag.retriever import HybridRetriever
from app.rag.context_builder import ContextBuilder

@pytest.mark.asyncio
async def test_hybrid_retriever_empty(test_db):
    retriever = HybridRetriever(test_db)
    results = await retriever.retrieve("non_existent_repo_id", "Where is auth implemented?", top_k=5)
    assert isinstance(results, list)
    assert len(results) == 0

def test_context_builder_budgeting():
    chunks = [
        {
            "file_path": "src/auth/AuthProvider.ts",
            "start_line": 1,
            "end_line": 20,
            "symbol_name": "AuthProvider",
            "symbol_type": "function",
            "content": "export const AuthProvider = () => { return null; };"
        }
    ]
    context_str = ContextBuilder.assemble_context(chunks, max_chars=1000)
    assert "src/auth/AuthProvider.ts" in context_str
    assert "AuthProvider" in context_str
