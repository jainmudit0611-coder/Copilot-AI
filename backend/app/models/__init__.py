"""
CodePilot AI Models Package.
Imports all models to ensure complete SQLAlchemy declarative metadata registration.
"""
from app.models.base import BaseModelMixin
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.repository import Repository, IndexStatus
from app.models.file import RepositoryFile, CodeChunk, CodeSymbol, CodeRelationship
from app.models.chat import Conversation, Message, CodeReview, BugAnalysis, AIRun, EvaluationRun

__all__ = [
    "BaseModelMixin",
    "User",
    "Workspace",
    "WorkspaceMember",
    "Repository",
    "IndexStatus",
    "RepositoryFile",
    "CodeChunk",
    "CodeSymbol",
    "CodeRelationship",
    "Conversation",
    "Message",
    "CodeReview",
    "BugAnalysis",
    "AIRun",
    "EvaluationRun",
]
