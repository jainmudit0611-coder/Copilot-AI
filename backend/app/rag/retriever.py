import json
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.file import CodeChunk, RepositoryFile, CodeSymbol
from app.providers.factory import get_embedding_provider

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if (norm1 * norm2) > 0 else 0.0

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def retrieve(
        self,
        repository_id: str,
        query: str,
        top_k: int = 5,
        language_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Generate query embedding
        query_vec = await self.embedding_provider.generate_embedding(query)

        # 2. Vector similarity search across DB chunks
        stmt = select(CodeChunk).where(CodeChunk.repository_id == repository_id)
        if language_filter:
            stmt = stmt.where(CodeChunk.language == language_filter)

        result = await self.db.execute(stmt)
        all_chunks = result.scalars().all()

        vector_results = []
        query_words = set(query.lower().split())

        for chunk in all_chunks:
            # Parse embedding
            chunk_vec = []
            if chunk.embedding_json:
                try:
                    chunk_vec = json.loads(chunk.embedding_json)
                except Exception:
                    pass

            score = cosine_similarity(query_vec, chunk_vec) if chunk_vec else 0.0

            # 3. Keyword / Symbol match bonus
            content_lower = chunk.content.lower()
            keyword_matches = sum(1 for word in query_words if word in content_lower)
            keyword_score = keyword_matches / max(1, len(query_words))

            # Reciprocal Rank / Hybrid Combined Score
            combined_score = (0.7 * score) + (0.3 * keyword_score)

            vector_results.append({
                "chunk_id": chunk.id,
                "file_path": chunk.file_path,
                "language": chunk.language,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol_name": chunk.symbol_name,
                "symbol_type": chunk.symbol_type,
                "content": chunk.content,
                "score": combined_score
            })

        # Sort by score descending
        vector_results.sort(key=lambda x: x["score"], reverse=True)
        return vector_results[:top_k]
