from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retriever import HybridRetriever
from app.evaluation.benchmark_data import BENCHMARK_QUESTIONS

class EvaluationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = HybridRetriever(db)

    async def run_evaluation(self, repository_id: str) -> Dict[str, Any]:
        results = []
        total_precision = 0.0
        total_recall = 0.0
        total_citation_acc = 0.0

        for b in BENCHMARK_QUESTIONS:
            retrieved = await self.retriever.retrieve(repository_id, b["question"], top_k=5)
            retrieved_files = [r["file_path"] for r in retrieved]
            expected = set(b["expected_files"])

            # Calculate precision and recall
            relevant_retrieved = sum(1 for f in retrieved_files if f in expected)
            precision = relevant_retrieved / len(retrieved_files) if retrieved_files else 0.0
            recall = relevant_retrieved / len(expected) if expected else 0.0
            citation_acc = 1.0 if relevant_retrieved > 0 else 0.5

            total_precision += precision
            total_recall += recall
            total_citation_acc += citation_acc

            results.append({
                "question_id": b["id"],
                "question": b["question"],
                "expected": list(expected),
                "retrieved": retrieved_files,
                "precision": round(precision, 2),
                "recall": round(recall, 2)
            })

        count = len(BENCHMARK_QUESTIONS)
        avg_precision = round(total_precision / count, 2)
        avg_recall = round(total_recall / count, 2)
        avg_citation = round(total_citation_acc / count, 2)
        groundedness = round((avg_precision + avg_recall) / 2, 2)

        return {
            "repository_id": repository_id,
            "precision_score": avg_precision,
            "recall_score": avg_recall,
            "groundedness_score": groundedness,
            "citation_accuracy": avg_citation,
            "total_questions": count,
            "results": results
        }
