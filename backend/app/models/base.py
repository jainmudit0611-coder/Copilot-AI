from app.core.database import Base
from sqlalchemy import Column, DateTime, String
import uuid
from datetime import datetime

def generate_uuid() -> str:
    return str(uuid.uuid4())

class BaseModelMixin:
    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
