from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.chat import EvaluationRun
from app.api.deps import get_current_user
from app.evaluation.eval_engine import EvaluationEngine

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

@router.post("/run/{repo_id}")
async def trigger_evaluation(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    eval_engine = EvaluationEngine(db)
    result = await eval_engine.run_evaluation(repo_id)

    eval_rec = EvaluationRun(
        repository_id=repo_id,
        precision_score=result["precision_score"],
        recall_score=result["recall_score"],
        groundedness_score=result["groundedness_score"],
        citation_accuracy=result["citation_accuracy"],
        total_questions=result["total_questions"],
        results_json=result["results"]
    )
    db.add(eval_rec)
    await db.commit()
    await db.refresh(eval_rec)

    return result

@router.get("/{repo_id}")
async def get_latest_evaluation(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EvaluationRun).where(EvaluationRun.repository_id == repo_id).order_by(EvaluationRun.created_at.desc())
    res = await db.execute(stmt)
    latest = res.scalar_one_or_none()
    if not latest:
        # Generate default benchmark evaluation on the fly
        eval_engine = EvaluationEngine(db)
        return await eval_engine.run_evaluation(repo_id)

    return {
        "id": latest.id,
        "repository_id": latest.repository_id,
        "precision_score": latest.precision_score,
        "recall_score": latest.recall_score,
        "groundedness_score": latest.groundedness_score,
        "citation_accuracy": latest.citation_accuracy,
        "total_questions": latest.total_questions,
        "results": latest.results_json,
        "created_at": latest.created_at.isoformat()
    }
