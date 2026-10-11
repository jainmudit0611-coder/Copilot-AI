from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from app.core.database import Base
from app.models.base import BaseModelMixin

class RepositoryFile(Base, BaseModelMixin):
    __tablename__ = "files"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    path = Column(String, nullable=False, index=True)
    language = Column(String, nullable=False, index=True)
    size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

class CodeChunk(Base, BaseModelMixin):
    __tablename__ = "code_chunks"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False, index=True)
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    symbol_name = Column(String, nullable=True)
    symbol_type = Column(String, nullable=True) # function, class, method, etc.
    embedding_json = Column(Text, nullable=True) # JSON array fallback for sqlite or vector column in pgvector

class CodeSymbol(Base, BaseModelMixin):
    __tablename__ = "code_symbols"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False, index=True)
    file_path = Column(String, nullable=False)
    name = Column(String, nullable=False, index=True)
    symbol_type = Column(String, nullable=False) # function, class, interface, route, etc.
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    signature = Column(String, nullable=True)

class CodeRelationship(Base, BaseModelMixin):
    __tablename__ = "code_relationships"

    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    source_file_id = Column(String, ForeignKey("files.id"), nullable=False)
    target_file_id = Column(String, ForeignKey("files.id"), nullable=True)
    source_symbol = Column(String, nullable=False)
    target_symbol = Column(String, nullable=False)
    relationship_type = Column(String, nullable=False) # IMPORTS, CALLS, DEPENDS_ON, IMPLEMENTS
