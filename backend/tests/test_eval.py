import pytest
from app.evaluation.eval_engine import EvaluationEngine

@pytest.mark.asyncio
async def test_eval_engine_runner(test_db):
    eval_engine = EvaluationEngine(test_db)
    summary = await eval_engine.run_evaluation("demo_repo_id")
    assert "precision_score" in summary
    assert "recall_score" in summary
    assert "groundedness_score" in summary
    assert "citation_accuracy" in summary
    assert summary["total_questions"] == 5
