"""empty message

Revision ID: de794e875a96
Revises: 8e681e36a2d7
Create Date: 2021-11-01 12:35:14.713262

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'de794e875a96'
down_revision = '8e681e36a2d7'
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
    op.create_table('question_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('group_type', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('corevariable_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['corevariable_id'], ['core_variable.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('questionnaire_question')
    op.drop_table('visitor')
    op.add_column('answer', sa.Column('question_id', sa.Integer(), nullable=True))
    op.drop_constraint(None, 'answer', type_='foreignkey')
    op.create_foreign_key(None, 'answer', 'question', ['question_id'], ['id'])
    op.drop_column('answer', 'questionnairequestion_id')
    op.add_column('core_variable', sa.Column('name', sa.String(length=30), nullable=True))
    op.add_column('core_variable', sa.Column('abbreviation', sa.String(length=4), nullable=True))
    op.add_column('core_variable', sa.Column('description', sa.String(length=400), nullable=True))
    op.create_unique_constraint(None, 'core_variable', ['abbreviation'])
    op.drop_column('core_variable', 'abbreviation_corevariable')
    op.drop_column('core_variable', 'name_corevariable')
    op.drop_column('core_variable', 'description_corevariable')
    op.add_column('moderator', sa.Column('name', sa.String(length=30), nullable=True))
    op.drop_column('moderator', 'name_moderator')
    op.add_column('questionnaire', sa.Column('name', sa.String(length=64), nullable=True))
    op.add_column('questionnaire', sa.Column('code', sa.String(length=64), nullable=True))
    op.drop_column('questionnaire', 'code_questionnaire')
    op.drop_column('questionnaire', 'name_questionnaire')
    op.add_column('standard_question', sa.Column('question', sa.String(length=100), nullable=True))
    op.drop_column('standard_question', 'name_question')
    op.add_column('study', sa.Column('name', sa.String(length=64), nullable=True))
    op.add_column('study', sa.Column('description', sa.String(length=1000), nullable=True))
    op.add_column('study', sa.Column('technology', sa.String(length=50), nullable=True))
    op.drop_index('ix_study_name_study', table_name='study')
    op.create_index(op.f('ix_study_name'), 'study', ['name'], unique=True)
    op.drop_column('study', 'description_study')
    op.drop_column('study', 'technology_study')
    op.drop_column('study', 'name_study')
    op.add_column('utau_tmodel', sa.Column('name', sa.String(length=25), nullable=True))
    op.drop_index('ix_utau_tmodel_name_utautmodel', table_name='utau_tmodel')
    op.create_index(op.f('ix_utau_tmodel_name'), 'utau_tmodel', ['name'], unique=True)
    op.drop_column('utau_tmodel', 'name_utautmodel')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('utau_tmodel', sa.Column('name_utautmodel', sa.VARCHAR(length=25), nullable=True))
    op.drop_index(op.f('ix_utau_tmodel_name'), table_name='utau_tmodel')
    op.create_index('ix_utau_tmodel_name_utautmodel', 'utau_tmodel', ['name_utautmodel'], unique=False)
    op.drop_column('utau_tmodel', 'name')
    op.add_column('study', sa.Column('name_study', sa.VARCHAR(length=64), nullable=True))
    op.add_column('study', sa.Column('technology_study', sa.VARCHAR(length=50), nullable=True))
    op.add_column('study', sa.Column('description_study', sa.VARCHAR(length=300), nullable=True))
    op.drop_index(op.f('ix_study_name'), table_name='study')
    op.create_index('ix_study_name_study', 'study', ['name_study'], unique=False)
    op.drop_column('study', 'technology')
    op.drop_column('study', 'description')
    op.drop_column('study', 'name')
    op.add_column('standard_question', sa.Column('name_question', sa.VARCHAR(length=100), nullable=True))
    op.drop_column('standard_question', 'question')
    op.add_column('questionnaire', sa.Column('name_questionnaire', sa.VARCHAR(length=64), nullable=True))
    op.add_column('questionnaire', sa.Column('code_questionnaire', sa.VARCHAR(length=64), nullable=True))
    op.drop_column('questionnaire', 'code')
    op.drop_column('questionnaire', 'name')
    op.add_column('moderator', sa.Column('name_moderator', sa.VARCHAR(length=30), nullable=True))
    op.drop_column('moderator', 'name')
    op.add_column('core_variable', sa.Column('description_corevariable', sa.VARCHAR(length=150), nullable=True))
    op.add_column('core_variable', sa.Column('name_corevariable', sa.VARCHAR(length=30), nullable=True))
    op.add_column('core_variable', sa.Column('abbreviation_corevariable', sa.VARCHAR(length=4), nullable=True))
    op.drop_constraint(None, 'core_variable', type_='unique')
    op.drop_column('core_variable', 'description')
    op.drop_column('core_variable', 'abbreviation')
    op.drop_column('core_variable', 'name')
    op.add_column('answer', sa.Column('questionnairequestion_id', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'answer', type_='foreignkey')
    op.create_foreign_key(None, 'answer', 'questionnaire_question', ['questionnairequestion_id'], ['id'])
    op.drop_column('answer', 'question_id')
    op.create_table('visitor',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('session_visitor', sa.VARCHAR(length=60), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_visitor')
    )
    op.create_table('questionnaire_question',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name_question', sa.VARCHAR(length=100), nullable=True),
    sa.Column('questionnaire_id', sa.INTEGER(), nullable=True),
    sa.Column('corevariable_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['corevariable_id'], ['core_variable.id'], ),
    sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaire.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('question_group')
    op.drop_table('question_type')
    op.drop_table('question')
    op.drop_index(op.f('ix_case_start'), table_name='case')
    op.drop_index(op.f('ix_case_age'), table_name='case')
    op.drop_table('case')
    # ### end Alembic commands ###
