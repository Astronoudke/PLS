"""empty message

Revision ID: 5ccba4ffa77a
Revises: 68def1c3654b
Create Date: 2021-11-02 10:25:13.116862

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '5ccba4ffa77a'
down_revision = '68def1c3654b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('code', sa.Text(), nullable=True))
    op.add_column('study', sa.Column('completed_cases', sa.Integer(), nullable=True))
    op.create_unique_constraint(None, 'study', ['code'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'study', type_='unique')
    op.drop_column('study', 'completed_cases')
    op.drop_column('study', 'code')
    # ### end Alembic commands ###
