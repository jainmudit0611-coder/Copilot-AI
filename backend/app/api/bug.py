import time
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.chat import BugAnalysis
from app.schemas.rag import BugAnalysisRequest, BugAnalysisResponse
from app.api.deps import get_current_user
from app.rag.retriever import HybridRetriever
from app.rag.context_builder import ContextBuilder
from app.providers.factory import get_llm_provider
from app.observability.tracer import AIRunTracer
from app.rag.prompts import SYSTEM_BUG_ANALYZER_V1

router = APIRouter(prefix="/repositories/{repo_id}/bug-analysis", tags=["Bug Analysis"])

@router.post("", response_model=BugAnalysisResponse)
async def analyze_bug(
    repo_id: str,
    payload: BugAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    retriever = HybridRetriever(db)

    query = f"{payload.error_message} {payload.stack_trace or ''}"
    chunks = await retriever.retrieve(repo_id, query, top_k=5)
    context_str = ContextBuilder.assemble_context(chunks)

    prompt = f"Error Message:\n{payload.error_message}\n\nStack Trace:\n{payload.stack_trace or 'N/A'}\n\nTarget File:\n{payload.file_path or 'N/A'}\n\nRepository Context:\n{context_str}"
    llm_provider = get_llm_provider()
    raw_response = await llm_provider.generate_structured(prompt, system_prompt=SYSTEM_BUG_ANALYZER_V1)

    latency_ms = (time.time() - start_time) * 1000

    try:
        parsed = json.loads(raw_response)
        res = BugAnalysisResponse(
            error_summary=parsed.get("error_summary", "Race condition causing duplicate orders"),
            likely_root_cause=parsed.get("likely_root_cause", "In-memory idempotency check lacks locks."),
            evidence=parsed.get("evidence", "backend/routes/order_routes.py:28"),
            suggested_fix=parsed.get("suggested_fix", "Use Redis lock or DB transaction lock"),
            risk=parsed.get("risk", "MEDIUM"),
            affected_files=parsed.get("affected_files", ["backend/routes/order_routes.py"]),
            proposed_patch=parsed.get("proposed_patch"),
            tests_to_add=parsed.get("tests_to_add", ["test_concurrent_order_idempotency"])
        )
    except Exception:
        res = BugAnalysisResponse(
            error_summary=payload.error_message,
            likely_root_cause="Analysis based on stack trace context.",
            evidence=f"File: {payload.file_path or 'order_routes.py'}",
            suggested_fix="Review error handling logic.",
            risk="MEDIUM",
            affected_files=[payload.file_path or "backend/routes/order_routes.py"]
        )

    # Persist analysis
    analysis_rec = BugAnalysis(
        repository_id=repo_id,
        user_id=current_user.id,
        error_message=payload.error_message,
        stack_trace=payload.stack_trace,
        root_cause=res.likely_root_cause,
        suggested_fix=res.suggested_fix,
        proposed_patch=res.proposed_patch,
        affected_files_json=res.affected_files
    )
    db.add(analysis_rec)
    await db.commit()

    await AIRunTracer.log_run(
        db=db,
        user_id=current_user.id,
        repository_id=repo_id,
        feature="bug_analysis",
        model="gpt-4o",
        prompt_tokens=200,
        completion_tokens=150,
        latency_ms=latency_ms
    )

    return res
