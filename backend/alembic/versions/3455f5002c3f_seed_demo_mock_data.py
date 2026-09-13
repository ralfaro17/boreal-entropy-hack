"""seed_demo_mock_data

Revision ID: 3455f5002c3f
Revises: 0a0471e92ec1
Create Date: 2026-09-13 04:47:18.999401

"""
import os
import sys
from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

# Ensure backend directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from seed import clean_database, seed_database

# revision identifiers, used by Alembic.
revision: str = '3455f5002c3f'
down_revision: Union[str, Sequence[str], None] = '0a0471e92ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed demo mock data for the 10 personas."""
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        seed_database(session, reset=False)
    finally:
        session.close()


def downgrade() -> None:
    """Remove seeded demo mock data."""
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        clean_database(session)
    finally:
        session.close()
