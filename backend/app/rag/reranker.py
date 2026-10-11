from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import CodeRelationship

class SymbolReranker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def expand_and_rerank(
        self,
        repository_id: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Boost items with matching symbol names and include imported target relationships
        stmt = select(CodeRelationship).where(CodeRelationship.repository_id == repository_id)
        res = await self.db.execute(stmt)
        relationships = res.scalars().all()

        import_map = {}
        for rel in relationships:
            import_map.setdefault(rel.source_file_path, []).append(rel.target_symbol)

        for chunk in retrieved_chunks:
            path = chunk["file_path"]
            if path in import_map:
                # Give small relationship connectivity boost
                chunk["score"] *= 1.15

        retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_chunks
