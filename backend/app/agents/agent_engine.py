import json
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.tools.repository_tools import RepositoryTools
from app.tools.code_tools import CodeTools
from app.providers.factory import get_llm_provider
from app.rag.context_builder import ContextBuilder
from app.schemas.rag import Citation, AgentToolCall, AgentRunResult

class AgentEngine:
    def __init__(self, db: AsyncSession, repository_id: str):
        self.db = db
        self.repository_id = repository_id
        self.repo_tools = RepositoryTools(db, repository_id)
        self.llm_provider = get_llm_provider()

    async def execute_agent(self, user_query: str, max_steps: int = 5) -> AgentRunResult:
        steps_taken: List[AgentToolCall] = []
        retrieved_contexts: List[Dict[str, Any]] = []

        # Step 1: Initial Repository Search
        search_results = await self.repo_tools.search_repository(user_query, top_k=5)
        steps_taken.append(AgentToolCall(
            tool_name="search_repository",
            arguments={"query": user_query, "top_k": 5},
            output={"results_count": len(search_results)}
        ))
        retrieved_contexts.extend(search_results)

        # Step 2: Inspect top file if available
        if search_results:
            top_file = search_results[0]["file_path"]
            file_data = await self.repo_tools.get_file(top_file, start_line=1, end_line=100)
            steps_taken.append(AgentToolCall(
                tool_name="get_file",
                arguments={"file_path": top_file, "start_line": 1, "end_line": 100},
                output={"path": top_file, "lines": 100}
            ))
            if "content" in file_data:
                analysis = CodeTools.run_static_analysis(top_file, file_data["content"])
                steps_taken.append(AgentToolCall(
                    tool_name="run_static_analysis",
                    arguments={"file_path": top_file},
                    output=analysis
                ))

        # Build combined context
        context_str = ContextBuilder.assemble_context(retrieved_contexts)

        # Synthesize final answer via LLM
        prompt = f"User Question: {user_query}\n\nRepository Evidence Context:\n{context_str}"
        raw_llm_output = await self.llm_provider.generate_structured(
            prompt,
            system_prompt="You are CodePilot AI Agent. Respond in structured JSON matching answer, citations, confidence, and reasoning_summary."
        )

        try:
            parsed = json.loads(raw_llm_output)
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
            return AgentRunResult(
                answer=parsed.get("answer", "Analysis complete."),
                citations=citations,
                steps_taken=steps_taken,
                reasoning_summary=parsed.get("reasoning_summary", f"Executed {len(steps_taken)} tool calls across indexed repository AST and vector chunks.")
            )
        except Exception:
            citations = [
                Citation(file=ctx["file_path"], start_line=ctx["start_line"], end_line=ctx["end_line"], relevance=ctx["score"])
                for ctx in retrieved_contexts[:3]
            ]
            return AgentRunResult(
                answer=raw_llm_output,
                citations=citations,
                steps_taken=steps_taken,
                reasoning_summary=f"Executed {len(steps_taken)} autonomous tool calls across indexed repository."
            )
