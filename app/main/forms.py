from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, RadioField, Label
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User, CoreVariable
from flask_login import current_user


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=0, max=64)])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('This username has already been taken. Please use a different one.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class CreateNewQuestionUser(FlaskForm):
    name_question = StringField('The Question', validators=[DataRequired(), Length(min=0, max=100)])
    submit = SubmitField('Create Question')


class GoToStartQuestionlist(FlaskForm):
    submit = SubmitField('Start Questionnaire')


# _______________________________________________________________________________________________________
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# _______________________________________________________________________________________________________


class DemographicsForm(FlaskForm):
    sex = SelectField(u'Sex')
    age = StringField('Age')
    submit = SubmitField('Create Case')


def DynamicTestForm(questions, *args, **kwargs):
    class TestForm(FlaskForm):
        submit = SubmitField('Go to next page')

    for name, value in questions.items():
        setattr(TestForm, name, value)

    return TestForm(*args, **kwargs)
