import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.models.user import User
from app.models.repository import Repository, IndexStatus
from app.models.workspace import Workspace, WorkspaceMember
from app.models.file import RepositoryFile, CodeChunk, CodeSymbol, CodeRelationship
from app.schemas.repository import RepositoryCreate, RepositoryResponse, FileNode, FileDetail, IndexingJobResponse
from app.task_queue.redis_queue import RedisJobQueue, DuplicateJobError, RedisQueueUnavailableError
from app.api.deps import get_current_user
from app.ingestion.scanner import RepositoryScanner
from app.ingestion.parser import CodeParser
from app.ingestion.chunker import IntelligentChunker
from app.ingestion.graph_builder import GraphBuilder
from app.ingestion.secret_scanner import scan_and_redact_secrets
from app.providers.factory import get_embedding_provider

router = APIRouter(prefix="/repositories", tags=["Repositories"])


async def verify_repository_access(repo: Repository, current_user: User, db: AsyncSession) -> None:
    """Verify that current_user has access to the repository's workspace."""
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # In local development/demo environment, allow access to default demo workspace
    if repo.workspace_id == "default-ws":
        return

    ws = await db.get(Workspace, repo.workspace_id)
    if not ws:
        return

    if ws.owner_id == current_user.id:
        return

    member_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == repo.workspace_id,
        WorkspaceMember.user_id == current_user.id
    )
    res = await db.execute(member_stmt)
    if res.scalar_one_or_none():
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You do not have access to this repository."
    )


async def run_repository_indexing(repository_id: str, source_dir: str, db_session_factory):
    async with db_session_factory() as db:
        try:
            # Update status -> DOWNLOADING / PARSING
            repo = await db.get(Repository, repository_id)
            if not repo:
                logger.warning("Repository %s not found in DB! Exiting indexing.", repository_id)
                return

            logger.info("Indexing repo %s: stage PARSING", repository_id)
            repo.status = IndexStatus.PARSING
            await db.commit()

            # 1. Scan directory
            files_data = RepositoryScanner.scan_directory(source_dir)
            logger.info("Scanned %d files for repo %s", len(files_data), repository_id)

            # 2. Clear old indexing data for this repository
            await db.execute(CodeRelationship.__table__.delete().where(CodeRelationship.repository_id == repository_id))
            await db.execute(CodeSymbol.__table__.delete().where(CodeSymbol.repository_id == repository_id))
            await db.execute(CodeChunk.__table__.delete().where(CodeChunk.repository_id == repository_id))
            await db.execute(RepositoryFile.__table__.delete().where(RepositoryFile.repository_id == repository_id))
            await db.commit()

            repo.status = IndexStatus.CHUNKING
            await db.commit()
            logger.info("Indexing repo %s: stage CHUNKING", repository_id)

            embedding_provider = get_embedding_provider()
            logger.info("Using embedding provider: %s", type(embedding_provider).__name__)
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
            logger.info("Indexing repo %s: stage EMBEDDING (%d chunks)", repository_id, len(all_chunks))

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
                    source_file_id=file_objs[0].id if file_objs else repository_id,
                    source_symbol=rel["source_symbol"],
                    target_symbol=rel["target_symbol"],
                    relationship_type=rel["relationship_type"]
                )
                db.add(rel_rec)

            repo.status = IndexStatus.COMPLETED
            repo.indexed_files_count = len(files_data)
            repo.indexed_chunks_count = len(all_chunks)
            repo.last_indexed_at = datetime.utcnow().isoformat()
            logger.info("Indexing repo %s: stage COMPLETED (%d files, %d chunks)", repository_id, len(files_data), len(all_chunks))
            repo.summary = {
                "languages": list(set(f["language"] for f in files_data)),
                "total_symbols": len(all_symbols),
                "total_relationships": len(relationships)
            }
            await db.commit()
        except Exception as e:
            logger.error("Indexing pipeline failed for repository %s: %s", repository_id, e, exc_info=True)
            await db.rollback()
            try:
                repo = await db.get(Repository, repository_id)
                if repo:
                    repo.status = IndexStatus.FAILED
                    await db.commit()
            except Exception:
                pass
            raise

@router.post("", response_model=RepositoryResponse)
async def create_repository(
    payload: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if payload.workspace_id and payload.workspace_id != "default-ws":
        ws = await db.get(Workspace, payload.workspace_id)
        if ws and ws.owner_id != current_user.id:
            member_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == payload.workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
            res = await db.execute(member_stmt)
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not have permission to add repositories to this workspace."
                )

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await verify_repository_access(repo, current_user, db)

    # Determine source directory (use demo-repository directory if demo repo)
    demo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../demo-repository"))
    source_dir = demo_dir if os.path.exists(demo_dir) else "."

    if settings.QUEUE_MODE == "redis":
        # 1. Verify Redis connectivity - fail clearly when requested queue is unavailable
        redis = await get_redis_client()
        if redis is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "REDIS_UNAVAILABLE",
                    "message": "Redis queue service is unavailable. Please verify REDIS_URL or start Redis."
                }
            )

        # 2. Enqueue job with distributed deduplication lock
        try:
            job = await RedisJobQueue.enqueue_indexing_job(
                repository_id=repo_id,
                user_id=current_user.id,
                source_dir=source_dir,
                max_retries=settings.INDEXING_JOB_MAX_RETRIES
            )
        except DuplicateJobError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "INDEXING_IN_PROGRESS", "message": str(exc)}
            )

        repo.status = IndexStatus.PENDING
        await db.commit()

        return {
            "status": "QUEUED",
            "job_id": job["id"],
            "repository_id": repo_id,
            "queue": "redis",
            "message": "Indexing job enqueued in Redis. A separate worker process will execute it."
        }
    else:
        # Explicit local dev mode using FastAPI BackgroundTasks
        repo.status = IndexStatus.DOWNLOADING
        await db.commit()
        from app.core.database import AsyncSessionLocal
        background_tasks.add_task(run_repository_indexing, repo_id, source_dir, AsyncSessionLocal)

        return {
            "status": "INDEXING_STARTED",
            "job_id": None,
            "repository_id": repo_id,
            "queue": "in_memory",
            "message": "Indexing started via in-process BackgroundTasks (QUEUE_MODE != redis)."
        }

@router.get("/{repo_id}/jobs/{job_id}", response_model=IndexingJobResponse)
async def get_indexing_job_status(
    repo_id: str,
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await verify_repository_access(repo, current_user, db)

    job = await RedisJobQueue.get_job(job_id)
    if not job:
        # Fallback to database record if job expired from Redis or in-memory mode was used
        return IndexingJobResponse(
            id=job_id,
            repository_id=repo_id,
            status=repo.status.lower(),
            stage=repo.status,
            retry_count=0,
            error=None
        )

    if job.get("repository_id") != repo_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job does not belong to specified repository."
        )

    return IndexingJobResponse(
        id=job["id"],
        repository_id=job["repository_id"],
        status=job["status"],
        stage=job["stage"],
        retry_count=job.get("retry_count", 0),
        created_at=job.get("created_at"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error=job.get("error")
    )

@router.get("/{repo_id}/files", response_model=List[FileNode])
async def list_files(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await verify_repository_access(repo, current_user, db)

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
async def get_file_detail(
    repo_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await verify_repository_access(repo, current_user, db)

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
