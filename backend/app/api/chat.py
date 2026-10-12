import time
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.repository import Repository
from app.schemas.rag import ChatRequest, StructuredAIResponse, Citation
from app.api.deps import get_current_user
from app.api.repository import verify_repository_access
from app.rag.retriever import HybridRetriever
from app.rag.context_builder import ContextBuilder
from app.providers.factory import get_llm_provider
from app.core.config import settings
from app.observability.tracer import AIRunTracer
from app.security.injection_guard import PromptInjectionGuard

router = APIRouter(prefix="/repositories/{repo_id}/chat", tags=["Chat"])

@router.post("", response_model=StructuredAIResponse)
async def chat_with_repository(
    repo_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await verify_repository_access(repo, current_user, db)

    start_time = time.time()
    clean_message = PromptInjectionGuard.check_and_sanitize(payload.message)

    # 1. RAG Retrieval
    retriever = HybridRetriever(db)
    chunks = await retriever.retrieve(repo_id, clean_message, top_k=5)

    # 2. Context assembly
    context_str = ContextBuilder.assemble_context(chunks)

    # 3. LLM Generation
    prompt = f"User Question: {clean_message}\n\nRepository Evidence Context:\n{context_str}"
    llm_provider = get_llm_provider()
    raw_response = await llm_provider.generate_structured(prompt, system_prompt="You are CodePilot AI. Return answer, citations, confidence, reasoning_summary.")

    latency_ms = (time.time() - start_time) * 1000

    try:
        parsed = json.loads(raw_response)
        citations = [
            Citation(
                file=c.get("file", "README.md"),
                start_line=c.get("start_line", 1),
                end_line=c.get("end_line", 20),
                relevance=c.get("relevance", 0.9),
                snippet=c.get("snippet")
            )
            for c in parsed.get("citations", [])
        ]
        res = StructuredAIResponse(
            answer=parsed.get("answer", raw_response),
            citations=citations,
            confidence=parsed.get("confidence", 0.9),
            reasoning_summary=parsed.get("reasoning_summary", "Retrieved relevant AST code chunks and performed RAG synthesis."),
            limitations=parsed.get("limitations", [])
        )
    except Exception:
        citations = [
            Citation(file=c["file_path"], start_line=c["start_line"], end_line=c["end_line"], relevance=c["score"])
            for c in chunks[:3]
        ]
        res = StructuredAIResponse(
            answer=raw_response,
            citations=citations,
            confidence=0.85,
            reasoning_summary="Retrieved top code chunks from pgvector/hybrid retrieval.",
            limitations=[]
        )

    # Log AI run observability metric
    active_model = settings.AZURE_OPENAI_DEPLOYMENT if settings.LLM_PROVIDER == "azure" else "mock"
    await AIRunTracer.log_run(
        db=db,
        user_id=current_user.id,
        repository_id=repo_id,
        feature="chat",
        model=active_model,
        prompt_tokens=len(prompt.split()),
        completion_tokens=len(res.answer.split()),
        latency_ms=latency_ms
    )

    return res

@router.post("/stream")
async def chat_with_repository_stream(
    repo_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await verify_repository_access(repo, current_user, db)

    async def event_generator():
        retriever = HybridRetriever(db)
        chunks = await retriever.retrieve(repo_id, payload.message, top_k=3)
        context_str = ContextBuilder.assemble_context(chunks)

        llm_provider = get_llm_provider()
        prompt = f"User Question: {payload.message}\n\nRepository Context:\n{context_str}"
        output = await llm_provider.generate(prompt)

        # Stream chunk tokens
        words = output.split(" ")
        for word in words:
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
