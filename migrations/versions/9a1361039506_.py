"""empty message

Revision ID: 9a1361039506
Revises: fdefdead64ae
Create Date: 2021-11-08 11:27:06.174907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a1361039506'
down_revision = 'fdefdead64ae'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('case', sa.Column('completed', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('case', 'completed')
    # ### end Alembic commands ###