"""empty message

Revision ID: 74c7ac5b75a9
Revises: 6815a9f70381
Create Date: 2021-10-14 12:16:17.728485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74c7ac5b75a9'
down_revision = '6815a9f70381'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('question', sa.Column('corevariable_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'question', 'core_variable', ['corevariable_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'question', type_='foreignkey')
    op.drop_column('question', 'corevariable_id')
    # ### end Alembic commands ###
