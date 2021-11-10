"""empty message

Revision ID: 15c79f8bc176
Revises: 57b5c3a6f2f5
Create Date: 2021-10-18 14:26:01.919288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15c79f8bc176'
down_revision = '57b5c3a6f2f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('technology_study', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('study', 'technology_study')
    # ### end Alembic commands ###
