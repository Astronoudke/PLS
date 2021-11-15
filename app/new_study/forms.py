from flask_wtf import FlaskForm
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, RadioField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Length

from app.models import User


class CreateNewStudyForm(FlaskForm):
    style_name = {'style': 'width:175%;'}
    name_of_study = StringField('Name of the study (max. 200 characters)',
                                validators=[DataRequired(), Length(min=0, max=200)], render_kw=style_name)
    style_description = {'style': 'width:250%;', "rows": 20}
    description_of_study = TextAreaField('Description of the study (max. 3000 characters)',
                                         validators=[DataRequired(), Length(min=0, max=3000)],
                                         render_kw=style_description)
    technology_of_study = StringField('Relevant technology of the study (max. 75 characters)',
                                      validators=[DataRequired(), Length(min=0, max=75)])
    submit = SubmitField('Create Study')


class AddUserForm(FlaskForm):
    name_user = StringField('The username of the user', validators=[DataRequired()])
    submit = SubmitField('Add user')

    def validate_username(self):
        user = User.query.filter_by(username=self.name_user.data).first()
        if user is current_user:
            raise ValidationError('You are this user.')

        if user is not None:
            raise ValidationError('This user does not exist.')


class AddCoreVariable(FlaskForm):
    add_variable = SelectField(u'Added Variable')
    submit = SubmitField('Select New Variable')


class CreateNewCoreVariableForm(FlaskForm):
    name_corevariable = StringField('Name of the core variable', validators=[DataRequired(), Length(min=0, max=50)])
    abbreviation_corevariable = StringField('The abbreviation of the core variable', validators=[DataRequired(),
                                                                                                 Length(min=0, max=4)])
    description_corevariable = TextAreaField('The description of the core variable',
                                             validators=[Length(min=0, max=1000)])
    submit = SubmitField('Create Core Variable')


class CreateNewRelationForm(FlaskForm):
    abbreviation_influencer = StringField('The abbreviation of the influencer',
                                          validators=[DataRequired(), Length(min=0, max=4)])
    abbreviation_influenced = StringField('The abbreviation of the influenced',
                                          validators=[DataRequired(), Length(min=0, max=4)])
    submit = SubmitField('Create Relation')


class CreateNewQuestion(FlaskForm):
    name_question = StringField('The Question', validators=[DataRequired(), Length(min=0, max=100)])
    submit = SubmitField('Create Question')


class ScaleForm(FlaskForm):
    scale = IntegerField('The scale used for the questionnaire (f.e. "5" will mean a scale from 1 to 5)',
                         validators=[DataRequired()])
    submit = SubmitField('Go to questionnaire')

    def __init__(self, original_score, *args, **kwargs):
        super(ScaleForm, self).__init__(*args, **kwargs)
        self.original_name = original_score


class AddDemographic(FlaskForm):
    add_demographic = SelectField(u'Added Demographic')
    submit = SubmitField('Select New Demographic')


class ChooseNewModel(FlaskForm):
    new_model = SelectField(u'Different Model', coerce=int)
    submit = SubmitField('Choose Different Model')


class EditStudyForm(FlaskForm):
    style_name = {'style': 'width:175%;'}
    name_of_study = StringField('Name of the study (max. 200 characters)',
                                validators=[DataRequired(), Length(min=0, max=200)], render_kw=style_name)
    style_description = {'style': 'width:250%;', "rows": 20}
    description_of_study = TextAreaField('Description of the study (max. 3000 characters)',
                                         validators=[DataRequired(), Length(min=0, max=3000)],
                                         render_kw=style_description)
    technology_of_study = StringField('Relevant technology of the study (max. 75 letters)',
                                      validators=[DataRequired(), Length(min=0, max=75)])
    submit = SubmitField('Edit Study')

    def __init__(self, original_name, original_description, original_technology, *args, **kwargs):
        super(EditStudyForm, self).__init__(*args, **kwargs)
        self.original_name = original_name
        self.original_description = original_description
        self.original_technology = original_technology


class CreateNewDemographicForm(FlaskForm):
    style_name = {'style': 'width:175%;'}
    name_of_demographic = StringField('Name of the demographic (max. 40 characters)',
                                      validators=[DataRequired(), Length(min=0, max=40)], render_kw=style_name)
    style_description = {'style': 'width:250%;', "rows": 20}
    description_of_demographic = TextAreaField('Description of the demographic',
                                               validators=[DataRequired(), Length(min=0, max=500)],
                                               render_kw=style_description)
    optionality_of_demographic = BooleanField('Is the demographic optional?')
    type_of_demographic = RadioField('Relevant technology of the study (max. 75 letters)',
                                     choices=['open', 'multiplechoice', 'radio'], validators=[DataRequired(),
                                                                                                Length(min=0, max=75)])
    choices_of_demographic = StringField('The choices that go with the question')
    submit = SubmitField('Create Demographic')
