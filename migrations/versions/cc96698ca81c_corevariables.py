"""corevariables

Revision ID: cc96698ca81c
Revises: 7d3f9d2f54a0
Create Date: 2021-10-12 10:38:02.991398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc96698ca81c'
down_revision = '7d3f9d2f54a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('utau_tmodel',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name_utautmodel', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_utau_tmodel_name_utautmodel'), 'utau_tmodel', ['name_utautmodel'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_utau_tmodel_name_utautmodel'), table_name='utau_tmodel')
    op.drop_table('utau_tmodel')
    # ### end Alembic commands ###
