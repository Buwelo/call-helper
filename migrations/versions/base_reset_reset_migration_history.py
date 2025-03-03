"""Reset migration history

Revision ID: base_reset
Revises: 
Create Date: 2025-03-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'base_reset'
down_revision = None  # This makes it the base migration
branch_labels = None
depends_on = None


def upgrade():
    # This migration represents the current state of the database
    # No operations needed as the database already has this structure
    pass


def downgrade():
    # Since this represents the base state, downgrade would drop all tables
    # But we'll leave this empty for safety
    pass