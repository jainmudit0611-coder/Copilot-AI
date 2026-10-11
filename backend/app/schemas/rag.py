from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int
    relevance: float
    snippet: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class StructuredAIResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float
    reasoning_summary: str
    limitations: List[str] = []

class AgentToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any

class AgentRunResult(BaseModel):
    answer: str
    citations: List[Citation]
    steps_taken: List[AgentToolCall]
    reasoning_summary: str

class BugAnalysisRequest(BaseModel):
    error_message: str
    stack_trace: Optional[str] = None
    file_path: Optional[str] = None

class BugAnalysisResponse(BaseModel):
    error_summary: str
    likely_root_cause: str
    evidence: str
    suggested_fix: str
    risk: str
    affected_files: List[str]
    proposed_patch: Optional[str] = None
    tests_to_add: List[str] = []

class CodeReviewRequest(BaseModel):
    git_diff: Optional[str] = None
    file_paths: Optional[List[str]] = None

class ReviewFinding(BaseModel):
    severity: str # HIGH, MEDIUM, LOW
    category: str # Security, Performance, Bug, Maintainability, Type Safety
    file: str
    line: int
    description: str
    evidence: str
    recommendation: str
    confidence: float

class CodeReviewResponse(BaseModel):
    summary: str
    findings: List[ReviewFinding]

class TestGenerationRequest(BaseModel):
    file_path: str
    framework: str = "pytest" # pytest, vitest, jest

class TestGenerationResponse(BaseModel):
    framework: str
    test_code: str
    explanation: str

class DocGenerationRequest(BaseModel):
    doc_type: str = "readme" # readme, architecture, api, module

class DocGenerationResponse(BaseModel):
    doc_type: str
    content: str

class AIRunMetric(BaseModel):
    id: str
    feature: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    status: str
    created_at: str

class EvaluationSummary(BaseModel):
    id: str
    precision_score: float
    recall_score: float
    groundedness_score: float
    citation_accuracy: float
    total_questions: int
    created_at: str
