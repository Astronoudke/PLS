"""empty message

Revision ID: dc6367bc4959
Revises: 8f1accd4fdd4
Create Date: 2021-11-02 14:46:08.092601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc6367bc4959'
down_revision = '8f1accd4fdd4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('case', sa.Column('session_id', sa.String(), nullable=True))
    op.add_column('case', sa.Column('questionnaire_id', sa.Integer(), nullable=True))
    op.create_unique_constraint(None, 'case', ['session_id'])
    op.create_foreign_key(None, 'case', 'questionnaire', ['questionnaire_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'case', type_='foreignkey')
    op.drop_constraint(None, 'case', type_='unique')
    op.drop_column('case', 'questionnaire_id')
    op.drop_column('case', 'session_id')
    # ### end Alembic commands ###