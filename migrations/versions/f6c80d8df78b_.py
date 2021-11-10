"""empty message

Revision ID: f6c80d8df78b
Revises: a464eef88d7c
Create Date: 2021-10-12 11:18:42.855626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6c80d8df78b'
down_revision = 'a464eef88d7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'study', 'utau_tmodel', ['linked_model'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'study', type_='foreignkey')
    # ### end Alembic commands ###