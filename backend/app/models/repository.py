from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, JSON
from app.core.database import Base
from app.models.base import BaseModelMixin
import enum

class IndexStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Repository(Base, BaseModelMixin):
    __tablename__ = "repositories"

    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    github_url = Column(String, nullable=True)
    default_branch = Column(String, default="main")
    status = Column(String, default=IndexStatus.PENDING, nullable=False)
    indexed_files_count = Column(Integer, default=0)
    indexed_chunks_count = Column(Integer, default=0)
    summary = Column(JSON, nullable=True) # Architecture overview, entry points, etc.
    last_indexed_at = Column(String, nullable=True)
