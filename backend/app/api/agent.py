import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.schemas.rag import ChatRequest, AgentRunResult
from app.api.deps import get_current_user
from app.agents.agent_engine import AgentEngine
from app.observability.tracer import AIRunTracer

router = APIRouter(prefix="/repositories/{repo_id}/agent", tags=["Agent"])

@router.post("", response_model=AgentRunResult)
async def run_agent(
    repo_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    agent_engine = AgentEngine(db, repo_id)
    result = await agent_engine.execute_agent(payload.message)
    latency_ms = (time.time() - start_time) * 1000

    tools_used = [step.tool_name for step in result.steps_taken]
    await AIRunTracer.log_run(
        db=db,
        user_id=current_user.id,
        repository_id=repo_id,
        feature="agent",
        model="gpt-4o",
        prompt_tokens=250,
        completion_tokens=len(result.answer.split()),
        latency_ms=latency_ms,
        tools_used={"tools": tools_used}
    )

    return result
