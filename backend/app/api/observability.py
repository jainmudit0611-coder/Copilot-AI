from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.chat import AIRun
from app.schemas.rag import AIRunMetric
from app.api.deps import get_current_user

router = APIRouter(prefix="/ai-runs", tags=["Observability"])

@router.get("", response_model=List[AIRunMetric])
async def list_ai_runs(
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AIRun).order_by(AIRun.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [
        AIRunMetric(
            id=r.id,
            feature=r.feature,
            model=r.model,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            latency_ms=r.latency_ms,
            estimated_cost_usd=r.estimated_cost_usd,
            status=r.status,
            created_at=r.created_at.isoformat()
        )
        for r in runs
    ]

@router.get("/metrics/summary")
async def get_observability_summary(
    db: AsyncSession = Depends(get_db)
):
    stmt = select(
        func.count(AIRun.id),
        func.sum(AIRun.prompt_tokens + AIRun.completion_tokens),
        func.avg(AIRun.latency_ms),
        func.sum(AIRun.estimated_cost_usd)
    )
    res = await db.execute(stmt)
    row = res.one()

    total_runs = row[0] or 0
    total_tokens = row[1] or 0
    avg_latency = round(row[2] or 0.0, 2)
    total_cost = round(row[3] or 0.0, 4)

    return {
        "total_ai_queries": total_runs,
        "total_tokens_consumed": total_tokens,
        "average_latency_ms": avg_latency,
        "total_cost_usd": total_cost,
        "active_model": "gpt-4o / text-embedding-3-small"
    }
