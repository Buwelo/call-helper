"""merge multiple heads

Revision ID: 45a9bd7272c0
Revises: 2220a2da4d16, b62d2de8a7e3, base_reset
Create Date: 2025-03-03 09:44:48.091510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45a9bd7272c0'
down_revision = ('2220a2da4d16', 'b62d2de8a7e3', 'base_reset')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
