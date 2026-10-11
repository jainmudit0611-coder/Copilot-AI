import pytest
from app.agents.agent_engine import AgentEngine

@pytest.mark.asyncio
async def test_agent_engine_execution(test_db):
    engine = AgentEngine(test_db, "repo_101")
    result = await engine.execute_agent("Why is login failing?")
    assert result.answer is not None
    assert len(result.steps_taken) > 0
    assert result.steps_taken[0].tool_name == "search_repository"
