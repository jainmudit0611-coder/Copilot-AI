from pydantic import BaseModel
from typing import Optional, List, Any, Dict

class RepositoryCreate(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    default_branch: str = "main"

class RepositoryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    github_url: Optional[str]
    default_branch: str
    status: str
    indexed_files_count: int
    indexed_chunks_count: int
    summary: Optional[Dict[str, Any]]
    last_indexed_at: Optional[str]

class FileNode(BaseModel):
    id: str
    path: str
    language: str
    size_bytes: int
    summary: Optional[str]

class FileDetail(FileNode):
    content: str
