from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import AIRun
from app.observability.cost_calculator import CostCalculator
from typing import Optional, Dict, Any

class AIRunTracer:
    @staticmethod
    async def log_run(
        db: AsyncSession,
        user_id: str,
        feature: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        repository_id: Optional[str] = None,
        tools_used: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS"
    ) -> AIRun:
        cost = CostCalculator.calculate_cost(model, prompt_tokens, completion_tokens)
        run = AIRun(
            repository_id=repository_id,
            user_id=user_id,
            feature=feature,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=cost,
            tools_used_json=tools_used,
            status=status
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run
