from sqlalchemy import Column, String, Boolean, Enum
from app.core.database import Base
from app.models.base import BaseModelMixin
import enum

class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"

class User(Base, BaseModelMixin):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.DEVELOPER, nullable=False)
    github_token = Column(String, nullable=True) # Fernet encrypted
    is_active = Column(Boolean, default=True)
