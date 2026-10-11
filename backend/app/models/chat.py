from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float, Integer
from app.core.database import Base
from app.models.base import BaseModelMixin

class Conversation(Base, BaseModelMixin):
    __tablename__ = "conversations"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)

class Message(Base, BaseModelMixin):
    __tablename__ = "messages"

    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    citations_json = Column(JSON, nullable=True) # file:line references
    reasoning_summary = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

class CodeReview(Base, BaseModelMixin):
    __tablename__ = "code_reviews"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    diff_content = Column(Text, nullable=False)
    findings_json = Column(JSON, nullable=False)
    summary = Column(Text, nullable=False)

class BugAnalysis(Base, BaseModelMixin):
    __tablename__ = "bug_analyses"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=False)
    proposed_patch = Column(Text, nullable=True) # Unified diff
    affected_files_json = Column(JSON, nullable=False)

class AIRun(Base, BaseModelMixin):
    __tablename__ = "ai_runs"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feature = Column(String, nullable=False) # chat, bug_analysis, review, test_gen, doc_gen
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    estimated_cost_usd = Column(Float, default=0.0)
    tools_used_json = Column(JSON, nullable=True)
    status = Column(String, default="SUCCESS")

class EvaluationRun(Base, BaseModelMixin):
    __tablename__ = "evaluation_runs"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    precision_score = Column(Float, nullable=False)
    recall_score = Column(Float, nullable=False)
    groundedness_score = Column(Float, nullable=False)
    citation_accuracy = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    results_json = Column(JSON, nullable=False)
