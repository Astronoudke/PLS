"""followers

Revision ID: 852b2800f767
Revises: db9cd5bc7e4e
Create Date: 2021-10-01 14:01:08.110053

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '852b2800f767'
down_revision = 'db9cd5bc7e4e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###