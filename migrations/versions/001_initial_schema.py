"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-08 21:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Upgrade script creating database schema
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

def downgrade() -> None:
    pass
