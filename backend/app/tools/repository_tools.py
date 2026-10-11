from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import RepositoryFile, CodeSymbol, CodeRelationship
from app.rag.retriever import HybridRetriever

class RepositoryTools:
    def __init__(self, db: AsyncSession, repository_id: str):
        self.db = db
        self.repository_id = repository_id
        self.retriever = HybridRetriever(db)

    async def search_repository(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.retriever.retrieve(self.repository_id, query, top_k=top_k)

    async def get_file(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        stmt = select(RepositoryFile).where(
            RepositoryFile.repository_id == self.repository_id,
            RepositoryFile.path == file_path
        )
        res = await self.db.execute(stmt)
        file_obj = res.scalar_one_or_none()
        if not file_obj:
            return {"error": f"File '{file_path}' not found in repository."}

        lines = file_obj.content.splitlines()
        start = start_line or 1
        end = end_line or len(lines)
        sliced_lines = lines[start - 1:end]

        return {
            "path": file_obj.path,
            "language": file_obj.language,
            "start_line": start,
            "end_line": end,
            "content": "\n".join(sliced_lines)
        }

    async def get_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        stmt = select(CodeSymbol).where(
            CodeSymbol.repository_id == self.repository_id,
            CodeSymbol.name == symbol_name
        )
        res = await self.db.execute(stmt)
        symbols = res.scalars().all()
        return [
            {
                "name": s.name,
                "symbol_type": s.symbol_type,
                "file_path": s.file_path,
                "start_line": s.start_line,
                "end_line": s.end_line,
                "signature": s.signature
            }
            for s in symbols
        ]

    async def get_related_files(self, file_path: str) -> List[Dict[str, Any]]:
        stmt = select(CodeRelationship).where(
            CodeRelationship.repository_id == self.repository_id,
            CodeRelationship.source_file_path == file_path
        )
        res = await self.db.execute(stmt)
        relationships = res.scalars().all()
        return [
            {
                "source": r.source_file_path,
                "target_symbol": r.target_symbol,
                "relationship": r.relationship_type
            }
            for r in relationships
        ]
