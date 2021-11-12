from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, session
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, EmptyForm, CreateNewQuestionUser, DemographicsForm, GoToStartQuestionlist, DynamicTestForm
from app.models import User, Study, UTAUTmodel, CoreVariable, Relation, Questionnaire, StandardQuestion, Case, \
    QuestionGroup, Question, Answer, DemographicAnswer, Demographic
from app.main import bp
from app.main.functions import reverse_value
from random import randint
import uuid
from wtforms import StringField, RadioField, Label


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/not_authorized', methods=['GET', 'POST'])
@login_required
def not_authorized():
    return render_template("not_authorized.html", title='Not Authorized')


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template("index.html", title='Home Page')


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/current_studies', methods=['GET', 'POST'])
@login_required
def current_studies():
    studies = [study for study in Study.query.all() if current_user in study.linked_users]

    return render_template("current_studies.html", title='New Study', studies=studies)


@bp.route('/standard_questions/<username>', methods=['GET', 'POST'])
@login_required
def standard_questions(username):
    user = User.query.filter_by(username=username).first_or_404()
    studies = Study.query.all()
    corevariables = CoreVariable.query.all()
    questions = StandardQuestion.query.filter_by(user_id=user.id)

    return render_template("standard_questions.html", title='New Study', user=user, studies=studies,
                           corevariables=corevariables,
                           questions=questions)


@bp.route('/standard_questions/new_question_user/<name_corevariable>/<username>', methods=['GET', 'POST'])
@login_required
def new_question_user(name_corevariable, username):
    form = CreateNewQuestionUser()

    if form.validate_on_submit():
        core_variable = CoreVariable.query.filter_by(name=name_corevariable).first_or_404()
        user = User.query.filter_by(username=username).first_or_404()

        new_question = StandardQuestion(question=form.name_question.data,
                                        user_id=user.id,
                                        corevariable_id=core_variable.id)
        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for("main.standard_questions", username=username))

    return render_template("new_question_user.html", title="New Question", form=form)


@bp.route('/remove_standard_question/<id_question>', methods=['GET', 'POST'])
@login_required
def remove_standard_question(id_question):
    StandardQuestion.query.filter_by(id=id_question).delete()
    db.session.commit()

    return redirect(url_for('main.standard_questions', username=current_user.username))


# _________________________________________________________________________________________________________________
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# _________________________________________________________________________________________________________________

@bp.route('/clear_session/<study_code>', methods=['GET', 'POST'])
def clear_session(study_code):
    session.clear()

    return redirect(url_for('main.create_session', study_code=study_code))


@bp.route('/invalid_session', methods=['GET', 'POST'])
def invalid_session():
    return render_template("invalid_session.html", title='Invalid Session')


@bp.route('/d/e/<study_code>', methods=['GET', 'POST'])
def intro_questionlist(study_code):
    if "user" not in session:
        session["user"] = str(uuid.uuid4())
        session["study"] = study_code

    if session["user"] in [case.session_id for case in Case.query.all()]:
        flash('You are currently already in a session. Complete the questionnaire.')  # return eerste blok vragenpagina
        return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

    form = GoToStartQuestionlist()
    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic for demographic in questionnaire.linked_demographics]

    if form.validate_on_submit():
        return redirect(url_for('main.start_questionlist', study_code=study_code))

    return render_template('intro_questionlist.html', title="Intro: {}".format(study.name), study=study,
                           study_code=study_code, form=form, demographics=demographics)


@bp.route('/d/e/start/<study_code>', methods=['GET', 'POST'])
def start_questionlist(study_code):
    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    demographics_dict = {}
    demographics = [demographic for demographic in questionnaire.linked_demographics]
    for demographic in demographics:
        demographics_dict[demographic.name] = demographic.return_field()
    form = DynamicTestForm(demographics_dict)

    if form.validate_on_submit():
        if session["user"] in [case.session_id for case in Case.query.all()] and session["study"] == study_code:
            flash('You are currently already in a session. Complete the questionnaire.')
            return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

        study = Study.query.filter_by(code=study_code).first()
        questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
        case = Case(session_id=session["user"], questionnaire_id=questionnaire.id)
        db.session.add(case)
        db.session.commit()

        session["demographic_answers"] = []
        for (demographic, answer) in zip([demographic for demographic in demographics], form.data.values()):
                demographic_answer = DemographicAnswer(answer=answer, demographic_id=demographic.id,
                                                       case_id=Case.query.filter_by(session_id=session["user"]).first().id)
                session["demographic_answers"].append(demographic_answer)

        questiongroup_dict = {}
        questiongroups = [questiongroup for questiongroup in
                          QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]
        keys = range(len(questiongroups))
        for i in keys:
            questiongroup_dict[i] = questiongroups[i]

        session["questionlist_questiongroups"] = questiongroup_dict
        session["questionlist_maxamount"] = QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id).count()
        session["answers"] = []

        return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

    return render_template('start_questionlist.html', title="Start: {}".format(study.name), study=study, form=form)


@bp.route('/c/e/<study_code>/<questionlist_number>', methods=['GET', 'POST'])
def questionlist(study_code, questionlist_number):
    if int(questionlist_number) >= session['questionlist_maxamount']:
        return redirect(url_for('main.ending_questionlist', study_code=study_code))

    print(session["answers"])
    print(session["user"])

    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    questions_dict = {}
    questionlist = session["questionlist_questiongroups"][int(questionlist_number)]
    questions = [question for question in Question.query.filter_by(questiongroup_id=questionlist.id)]
    for question in questions:
        questions_dict[question.question] = RadioField(question.question, choices=[number for number in range(1, questionnaire.scale+1)])
    form = DynamicTestForm(questions_dict)

    next_questionlist_number = int(questionlist_number) + 1

    if form.validate_on_submit():
        for (question, value) in zip([question for question in questions], form.data.values()):
            if isinstance(value, str) and len(value) < 4:
                if question.id in [answer.question_id for answer in session["answers"]]:
                    for answer in session["answers"]:
                        if answer.question_id == question.id:
                            if question.reversed_score:
                                answer.score = reverse_value(value, questionnaire.scale)
                            else:
                                answer.score = value
                else:
                    if question.reversed_score:
                        answer = Answer(score=reverse_value(value, questionnaire.scale), question_id=question.id,
                                        case_id=Case.query.filter_by(session_id=session["user"]).first().id)
                        session["answers"].append(answer)
                    else:
                        answer = Answer(score=value, question_id=question.id,
                                        case_id=Case.query.filter_by(session_id=session["user"]).first().id)
                        session["answers"].append(answer)
        return redirect(
            url_for('main.questionlist', study_code=study_code, questionlist_number=next_questionlist_number))

    return render_template('questionlist.html',
                           title="Questionlist {}: {}".format(str(questionlist_number), study.name),
                           study=study, questionlist_number=questionlist_number, questions=questions,
                           questionlist=questionlist, next_questionlist_number=next_questionlist_number, form=form)


@bp.route('/g/e/<study_code>', methods=['GET', 'POST'])
def ending_questionlist(study_code):
    form = EmptyForm()
    if form.validate_on_submit():
        for answer in session["answers"]:
            db.session.add(answer)
            db.session.commit()
        for answer in session["demographic_answers"]:
            db.session.add(answer)
            db.session.commit()
        Case.query.filter_by(session_id=session["user"]).first().completed = True
        db.session.commit()
        session.clear()
        return "Thank you for participating."
    return render_template('ending_questionlist.html', title="Ending Questionnaire", form=form)


@bp.route('/beren', methods=['GET', 'POST'])
def test():
    questions = {
        'question_1': RadioField('Question 1', choices=[1, 2, 3, 4, 5]),
        'question_2': RadioField('Question 2', choices=[1, 2, 3, 4, 5])
    }

    form = DynamicTestForm(questions)
    return render_template('test.html', title="Test", form=form)
