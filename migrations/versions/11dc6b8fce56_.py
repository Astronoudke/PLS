"""empty message

Revision ID: 11dc6b8fce56
Revises: 9e7c8d1d708c
Create Date: 2021-10-12 11:26:35.080698

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '11dc6b8fce56'
down_revision = '9e7c8d1d708c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('model_id', sa.Integer(), nullable=True))
    op.drop_constraint(None, 'study', type_='foreignkey')
    op.create_foreign_key(None, 'study', 'utau_tmodel', ['model_id'], ['id'])
    op.drop_column('study', 'linked_model')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('linked_model', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'study', type_='foreignkey')
    op.create_foreign_key(None, 'study', 'utau_tmodel', ['linked_model'], ['id'])
    op.drop_column('study', 'model_id')
    # ### end Alembic commands ###
