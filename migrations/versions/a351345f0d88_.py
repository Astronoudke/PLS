"""empty message

Revision ID: a351345f0d88
Revises: de794e875a96
Create Date: 2021-11-01 12:37:15.490615

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a351345f0d88'
down_revision = 'de794e875a96'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('case',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start', sa.DateTime(), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('sex', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_age'), 'case', ['age'], unique=False)
    op.create_index(op.f('ix_case_start'), 'case', ['start'], unique=False)
    op.create_table('core_variable',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('abbreviation', sa.String(length=4), nullable=True),
    sa.Column('description', sa.String(length=400), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('abbreviation')
    )
    op.create_table('moderator',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question', sa.String(length=100), nullable=True),
    sa.Column('reversed_score', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('question_type',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('utau_tmodel',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_utau_tmodel_name'), 'utau_tmodel', ['name'], unique=True)
    op.create_table('answer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('score', sa.SmallInteger(), nullable=True),
    sa.Column('question_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    op.create_table('question_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('group_type', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('corevariable_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['corevariable_id'], ['core_variable.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('relation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.Column('influencer_id', sa.Integer(), nullable=True),
    sa.Column('influenced_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['influenced_id'], ['core_variable.id'], ),
    sa.ForeignKeyConstraint(['influencer_id'], ['core_variable.id'], ),
    sa.ForeignKeyConstraint(['model_id'], ['utau_tmodel.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('standard_question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question', sa.String(length=100), nullable=True),
    sa.Column('corevariable_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['corevariable_id'], ['core_variable.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('study',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('technology', sa.String(length=50), nullable=True),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
    sa.Column('is_underway', sa.Boolean(), nullable=True),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['model_id'], ['utau_tmodel.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_name'), 'study', ['name'], unique=True)
    op.create_table('utautmodel_corevariable',
    sa.Column('utau_tmodel_id', sa.Integer(), nullable=True),
    sa.Column('core_variable_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['core_variable_id'], ['core_variable.id'], ),
    sa.ForeignKeyConstraint(['utau_tmodel_id'], ['utau_tmodel.id'], )
    )
    op.create_table('questionnaire',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('code', sa.String(length=64), nullable=True),
    sa.Column('study_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('study_user',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('study_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('study_user')
    op.drop_table('questionnaire')
    op.drop_table('utautmodel_corevariable')
    op.drop_index(op.f('ix_study_name'), table_name='study')
    op.drop_table('study')
    op.drop_table('standard_question')
    op.drop_table('relation')
    op.drop_table('question_group')
    op.drop_table('followers')
    op.drop_table('answer')
    op.drop_index(op.f('ix_utau_tmodel_name'), table_name='utau_tmodel')
    op.drop_table('utau_tmodel')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('question_type')
    op.drop_table('question')
    op.drop_table('moderator')
    op.drop_table('core_variable')
    op.drop_index(op.f('ix_case_start'), table_name='case')
    op.drop_index(op.f('ix_case_age'), table_name='case')
    op.drop_table('case')
    # ### end Alembic commands ###
