from sqlalchemy import Column, String, ForeignKey
from app.core.database import Base
from app.models.base import BaseModelMixin

class Workspace(Base, BaseModelMixin):
    __tablename__ = "workspaces"

    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

class WorkspaceMember(Base, BaseModelMixin):
    __tablename__ = "workspace_members"

    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="DEVELOPER", nullable=False)
