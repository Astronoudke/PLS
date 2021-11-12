"""empty message

Revision ID: 68def1c3654b
Revises: 553b6eb9dbfd
Create Date: 2021-11-02 09:49:58.460151

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '68def1c3654b'
down_revision = '553b6eb9dbfd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('stage_1', sa.Boolean(), nullable=True))
    op.add_column('study', sa.Column('stage_2', sa.Boolean(), nullable=True))
    op.add_column('study', sa.Column('stage_3', sa.Boolean(), nullable=True))
    op.drop_column('study', 'is_underway')
    op.drop_column('study', 'is_completed')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('is_completed', sa.BOOLEAN(), nullable=True))
    op.add_column('study', sa.Column('is_underway', sa.BOOLEAN(), nullable=True))
    op.drop_column('study', 'stage_3')
    op.drop_column('study', 'stage_2')
    op.drop_column('study', 'stage_1')
    # ### end Alembic commands ###
