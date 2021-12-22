from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, RadioField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Length

from app.models import User


# De Form voor het aanpassen van het profiel van de eigen gebruiker.
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


# De Form welke gebruikt wordt voor enkel opslaan en verwijzen.
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


# De Form voor het creëren van een nieuwe standaardvraag.
class CreateNewQuestionUser(FlaskForm):
    name_question = StringField('The Question', validators=[DataRequired(), Length(min=0, max=100)])
    submit = SubmitField('Create Question')


# De knop om te starten met de vragenlijst.
class GoToStartQuestionlist(FlaskForm):
    submit = SubmitField('Start Questionnaire')


# De Form voor het creëren van een nieuwe demografiek binnen de vragenlijst.
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
    choices_of_demographic = StringField('The choices that go with the question (separated with a comma, no space)')
    submit = SubmitField('Create Demographic')


# _______________________________________________________________________________________________________
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# _______________________________________________________________________________________________________


# Een dynamische veld waarmee meerdere Forms tegelijk opgeslagen kunnen worden. Deze wordt met name gebruikt binnen de
# vragenlijst voor de RadioFields. De reden voor het gebruik van deze dynamische form is omdat bij sommige gedeeltes van
# de vragenlijst (zoals de hoeveelheid vragen binnen een kernvariabele en hoeveel demografische informatie opgeslagen)
# door de gebruiker zelf bepaald worden en dus de hoeveelheid onbepaald is voor de programmeur voorafgaand.
def DynamicTestForm(questions, *args, **kwargs):
    class TestForm(FlaskForm):
        submit = SubmitField('Go to next page')

    for name, value in questions.items():
        setattr(TestForm, name, value)

    return TestForm(*args, **kwargs)
