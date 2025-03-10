"""fresh migration after database reset

Revision ID: 016429e92fb9
Revises: 45a9bd7272c0
Create Date: 2025-03-03 09:59:10.341229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016429e92fb9'
down_revision = '45a9bd7272c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_transcript', schema=None) as batch_op:
        batch_op.add_column(sa.Column('benchmark_score', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_transcript', schema=None) as batch_op:
        batch_op.drop_column('benchmark_score')

    # ### end Alembic commands ###
