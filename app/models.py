from datetime import datetime
from hashlib import md5
from time import time
from datetime import datetime
import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from app import db, login
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

study_user = db.Table('study_user',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                      db.Column('study_id', db.Integer, db.ForeignKey('study.id'))
                      )

utautmodel_corevariable = db.Table('utautmodel_corevariable',
                                   db.Column('utau_tmodel_id', db.Integer, db.ForeignKey('utau_tmodel.id')),
                                   db.Column('core_variable_id', db.Integer, db.ForeignKey('core_variable.id'))
                                   )

questionnaire_demographic = db.Table('questionnaire_demographic',
                                     db.Column('questionnaire_id', db.Integer, db.ForeignKey('questionnaire.id')),
                                     db.Column('demographic_id', db.Integer, db.ForeignKey('demographic.id'))
                                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    linked_studies = db.relationship('Study', secondary=study_user, backref=db.backref('researchers'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def link(self, study):
        if not self.is_linked(study):
            self.linked_studies.append(study)

    def unlink(self, study):
        if self.is_linked(study):
            self.linked_studies.remove(study)

    def is_linked(self, study):
        return self.linked_studies.filter(
            study_user.c.study_id == study.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class UTAUTmodel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True)
    linked_corevariables = db.relationship('CoreVariable', secondary=utautmodel_corevariable,
                                           backref=db.backref('corevariables'), lazy='dynamic')

    def __repr__(self):
        return '<UTAUT model {}>'.format(self.name)


class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True, unique=True)
    description = db.Column(db.String(3000))
    technology = db.Column(db.String(75))
    code = db.Column(db.String, unique=True)
    # stage_1 is the stage in which the research is being set up and changes can be made
    stage_1 = db.Column(db.Boolean, default=True)
    # stage_2 is the stage in which the research is underway, but questionnaires are being put out and only very
    # limited changes can be made to the study.
    stage_2 = db.Column(db.Boolean, default=False)
    # stage_3 is the stage in which the study is completed, and no further changes can be made to the study.
    stage_3 = db.Column(db.Boolean, default=False)
    linked_users = db.relationship('User', secondary=study_user, backref=db.backref('researchers'), lazy='dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('utau_tmodel.id'))

    def __repr__(self):
        return '<Study {}>'.format(self.name_study)

    def change_model(self, new_model_id):
        self.model_id = new_model_id

    def create_code(self):
        self.code = str(uuid.uuid4())


class Questionnaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    code = db.Column(db.String(64))
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'))
    scale = db.Column(db.Integer)

    linked_questiongroups = db.relationship('QuestionGroup', backref='questionnaire_questiongroup',
                                            lazy='dynamic')
    linked_demographics = db.relationship('Demographic', secondary=questionnaire_demographic,
                                          backref=db.backref('demographics'), lazy='dynamic')

    def __repr__(self):
        return '<Questionnaire {}>'.format(self.name)

    def total_completed_cases(self):
        total = Case.query.filter_by(questionnaire_id=self.id, completed=True).count()
        return str(total)


class Demographic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), index=True, unique=True)
    questiontype_name = db.Column(db.String, db.ForeignKey('question_type.name'))
    choices = db.Column(db.String)
    optional = db.Column(db.Boolean, default=True)

    linked_questionnaires = db.relationship('Questionnaire', secondary=questionnaire_demographic,
                                            backref=db.backref('questionnaires'), lazy='dynamic')

    def __repr__(self):
        return '<Demographic {}>'.format(self.name)

    def link(self, questionnaire):
        if not self.is_linked(questionnaire):
            self.linked_questionnaires.append(questionnaire)

    def unlink(self, questionnaire):
        if self.is_linked(questionnaire):
            self.linked_questionnaires.remove(questionnaire)

    def is_linked(self, questionnaire):
        return self.linked_questionnaires.filter(
            questionnaire_demographic.c.questionnaire_id == questionnaire.id).count() > 0

    def return_field(self):
        if self.questiontype_name == "open":
            if self.optional:
                return StringField(self.name)
            return StringField(self.name, validators=[DataRequired()])
        elif self.questiontype_name == "multiplechoice":
            if self.optional:
                choices = self.choices.split(',')
                choices.append("No Answer")
                return SelectField(u'{}'.format(self.name), choices=choices)
            return SelectField(u'{}'.format(self.name), choices=self.choices.split(','))


class DemographicAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.String)
    demographic_id = db.Column(db.Integer, db.ForeignKey('demographic.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))

    def __repr__(self):
        demographic = Demographic.query.filter_by(id=self.demographic_id).first()
        return '<{}: {}>'.format(demographic.name, self.answer)


class StandardQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    corevariable_id = db.Column(db.Integer, db.ForeignKey('core_variable.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Question {}>'.format(self.question)


class QuestionType(db.Model):
    name = db.Column(db.String(64), primary_key=True)

    def __repr__(self):
        return '<Question type {}>'.format(self.name)


class QuestionGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    group_type = db.Column(db.String)
    description = db.Column(db.Text)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaire.id'))
    corevariable_id = db.Column(db.Integer, db.ForeignKey('core_variable.id'))

    def __repr__(self):
        return '<Question group {}>'.format(self.title)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    reversed_score = db.Column(db.Boolean, default=False)
    questiongroup_id = db.Column(db.Integer, db.ForeignKey('question_group.id'))

    answer_question = db.relationship('Answer', backref='answered_question',
                                      lazy='dynamic')

    def __repr__(self):
        return '<Question {}>'.format(self.question)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.SmallInteger)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))


class CoreVariable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    abbreviation = db.Column(db.String(4), unique=True)
    description = db.Column(db.String(1000))
    linked_models = db.relationship('UTAUTmodel', secondary=utautmodel_corevariable,
                                    backref=db.backref('models'), lazy='dynamic')

    def __repr__(self):
        return '<Core variable {}>'.format(self.name)

    def link(self, model):
        if not self.is_linked(model):
            self.linked_models.append(model)

    def unlink(self, model):
        if self.is_linked(model):
            self.linked_models.remove(model)

    def is_linked(self, model):
        return self.linked_models.filter(
            utautmodel_corevariable.c.utau_tmodel_id == model.id).count() > 0


class Relation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('utau_tmodel.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('core_variable.id'))
    influenced_id = db.Column(db.Integer, db.ForeignKey('core_variable.id'))
    influencer = db.relationship('CoreVariable', foreign_keys=[influencer_id])
    influenced = db.relationship('CoreVariable', foreign_keys=[influenced_id])

    def return_relation(self):
        return '{} ----> {}'.format(
            CoreVariable.query.get(self.influencer_id).name,
            CoreVariable.query.get(self.influenced_id).name)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, unique=True)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaire.id'))
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    completed = db.Column(db.Boolean, default=False)

    def print_demographics(self):
        for demographic_answer in [demographic for demographic in DemographicAnswer.query.filter_by(case_id=self.id)]:
            demographic = Demographic.query.filter_by(id=demographic_answer.demographic_id).first()
            print('{}: {}'.format(demographic.name, demographic_answer.answer))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
