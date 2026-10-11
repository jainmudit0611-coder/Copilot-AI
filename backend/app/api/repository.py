import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.repository import Repository, IndexStatus
from app.models.file import RepositoryFile, CodeChunk, CodeSymbol, CodeRelationship
from app.schemas.repository import RepositoryCreate, RepositoryResponse, FileNode, FileDetail
from app.api.deps import get_current_user
from app.ingestion.scanner import RepositoryScanner
from app.ingestion.parser import CodeParser
from app.ingestion.chunker import IntelligentChunker
from app.ingestion.graph_builder import GraphBuilder
from app.ingestion.secret_scanner import scan_and_redact_secrets
from app.providers.factory import get_embedding_provider

router = APIRouter(prefix="/repositories", tags=["Repositories"])

async def run_repository_indexing(repository_id: str, source_dir: str, db_session_factory):
    async with db_session_factory() as db:
        try:
            # Update status -> DOWNLOADING / PARSING
            repo = await db.get(Repository, repository_id)
            if not repo:
                return

            repo.status = IndexStatus.PARSING
            await db.commit()

            # 1. Scan directory
            files_data = RepositoryScanner.scan_directory(source_dir)

            # 2. Clear old indexing data for this repository
            await db.execute(CodeRelationship.__table__.delete().where(CodeRelationship.repository_id == repository_id))
            await db.execute(CodeSymbol.__table__.delete().where(CodeSymbol.repository_id == repository_id))
            await db.execute(CodeChunk.__table__.delete().where(CodeChunk.repository_id == repository_id))
            await db.execute(RepositoryFile.__table__.delete().where(RepositoryFile.repository_id == repository_id))
            await db.commit()

            repo.status = IndexStatus.CHUNKING
            await db.commit()

            embedding_provider = get_embedding_provider()
            file_objs = []
            all_chunks = []
            all_symbols = []

            for f_info in files_data:
                redacted_content = scan_and_redact_secrets(f_info["content"])
                file_rec = RepositoryFile(
                    repository_id=repository_id,
                    path=f_info["path"],
                    language=f_info["language"],
                    size_bytes=f_info["size_bytes"],
                    file_hash=f_info["file_hash"],
                    content=redacted_content
                )
                db.add(file_rec)
                await db.flush()
                file_objs.append(file_rec)

                # Extract AST symbols
                syms = CodeParser.extract_symbols(redacted_content, f_info["language"])
                for s in syms:
                    sym_rec = CodeSymbol(
                        repository_id=repository_id,
                        file_id=file_rec.id,
                        file_path=f_info["path"],
                        name=s["name"],
                        symbol_type=s["symbol_type"],
                        start_line=s["start_line"],
                        end_line=s["end_line"],
                        signature=s.get("signature")
                    )
                    db.add(sym_rec)
                    all_symbols.append(sym_rec)

                # Generate code chunks
                chunks = IntelligentChunker.chunk_file(f_info["path"], f_info["language"], redacted_content)
                for c in chunks:
                    all_chunks.append({
                        "file_id": file_rec.id,
                        "chunk": c
                    })

            await db.commit()

            repo.status = IndexStatus.EMBEDDING
            await db.commit()

            # Batch embeddings generation
            chunk_texts = [item["chunk"]["content"] for item in all_chunks]
            embeddings = await embedding_provider.generate_embeddings_batch(chunk_texts) if chunk_texts else []

            for item, emb in zip(all_chunks, embeddings):
                c = item["chunk"]
                chunk_rec = CodeChunk(
                    repository_id=repository_id,
                    file_id=item["file_id"],
                    file_path=c["file_path"],
                    language=c["language"],
                    start_line=c["start_line"],
                    end_line=c["end_line"],
                    symbol_name=c["symbol_name"],
                    symbol_type=c["symbol_type"],
                    content=c["content"],
                    embedding_json=json.dumps(emb)
                )
                db.add(chunk_rec)

            # Build code relationships
            relationships = GraphBuilder.extract_relationships(files_data)
            for rel in relationships:
                rel_rec = CodeRelationship(
                    repository_id=repository_id,
                    source_file_id=repository_id,
                    source_symbol=rel["source_symbol"],
                    target_symbol=rel["target_symbol"],
                    relationship_type=rel["relationship_type"]
                )
                db.add(rel_rec)

            repo.status = IndexStatus.COMPLETED
            repo.indexed_files_count = len(files_data)
            repo.indexed_chunks_count = len(all_chunks)
            repo.last_indexed_at = datetime.utcnow().isoformat()
            repo.summary = {
                "languages": list(set(f["language"] for f in files_data)),
                "total_symbols": len(all_symbols),
                "total_relationships": len(relationships)
            }
            await db.commit()
        except Exception as e:
            repo = await db.get(Repository, repository_id)
            if repo:
                repo.status = IndexStatus.FAILED
                await db.commit()

@router.post("", response_model=RepositoryResponse)
async def create_repository(
    payload: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = Repository(
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        github_url=payload.github_url,
        default_branch=payload.default_branch,
        status=IndexStatus.PENDING
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return RepositoryResponse(
        id=repo.id,
        workspace_id=repo.workspace_id,
        name=repo.name,
        description=repo.description,
        github_url=repo.github_url,
        default_branch=repo.default_branch,
        status=repo.status,
        indexed_files_count=repo.indexed_files_count,
        indexed_chunks_count=repo.indexed_chunks_count,
        summary=repo.summary,
        last_indexed_at=repo.last_indexed_at
    )

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Repository)
    if workspace_id:
        stmt = stmt.where(Repository.workspace_id == workspace_id)
    res = await db.execute(stmt)
    repos = res.scalars().all()

    if not repos:
        # Create demo repo automatically if none exists
        demo_repo = Repository(
            workspace_id=workspace_id or "default-ws",
            name="Demo Full-Stack Application",
            description="E-Commerce application with auth, order processing, and payment service.",
            github_url="https://github.com/example/demo-ecommerce",
            default_branch="main",
            status=IndexStatus.PENDING
        )
        db.add(demo_repo)
        await db.commit()
        await db.refresh(demo_repo)
        repos = [demo_repo]

    return [
        RepositoryResponse(
            id=r.id,
            workspace_id=r.workspace_id,
            name=r.name,
            description=r.description,
            github_url=r.github_url,
            default_branch=r.default_branch,
            status=r.status,
            indexed_files_count=r.indexed_files_count,
            indexed_chunks_count=r.indexed_chunks_count,
            summary=r.summary,
            last_indexed_at=r.last_indexed_at
        )
        for r in repos
    ]

@router.post("/{repo_id}/index")
async def trigger_indexing(
    repo_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.status = IndexStatus.DOWNLOADING
    await db.commit()

    # Determine source directory (use demo-repository directory if demo repo)
    demo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../demo-repository"))
    source_dir = demo_dir if os.path.exists(demo_dir) else "."

    from app.core.database import AsyncSessionLocal
    background_tasks.add_task(run_repository_indexing, repo_id, source_dir, AsyncSessionLocal)

    return {"status": "INDEXING_STARTED", "repository_id": repo_id}

@router.get("/{repo_id}/files", response_model=List[FileNode])
async def list_files(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    res = await db.execute(stmt)
    files = res.scalars().all()
    return [
        FileNode(
            id=f.id,
            path=f.path,
            language=f.language,
            size_bytes=f.size_bytes,
            summary=f.summary
        )
        for f in files
    ]

@router.get("/{repo_id}/files/{file_id:path}", response_model=FileDetail)
async def get_file_detail(repo_id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    # Support lookup by file_id OR path
    stmt = select(RepositoryFile).where(
        RepositoryFile.repository_id == repo_id,
        (RepositoryFile.id == file_id) | (RepositoryFile.path == file_id)
    )
    res = await db.execute(stmt)
    file_obj = res.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found in repository.")

    return FileDetail(
        id=file_obj.id,
        path=file_obj.path,
        language=file_obj.language,
        size_bytes=file_obj.size_bytes,
        summary=file_obj.summary,
        content=file_obj.content
    )
