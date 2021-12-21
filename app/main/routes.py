import uuid
from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from wtforms import RadioField

from app import db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, CreateNewQuestionUser, GoToStartQuestionlist, \
    CreateNewDemographicForm, DynamicTestForm
from app.main.functions import reverse_value
from app.models import User, Study, CoreVariable, Questionnaire, StandardQuestion, Case, \
    QuestionGroup, Question, Answer, DemographicAnswer, StandardDemographic, Demographic


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
    form = EmptyForm()
    return render_template('user.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # De Form voor het aanpassen van het profiel.
    form = EditProfileForm(current_user.username)

    # Als de gebruiker aangeeft aanpassingen te willen maken aan het profiel.
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        # Een Flash/bericht binnen de applicatie welke aangeeft dat de aanpassingen zijn gemaakt.
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    # Als (bij sommige gedeeltes) geen aanpassingen zijn gemaakt.
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


# De volgfuncties zijn (nog) niet toegepast binnen de applicatie. Deze functie zou toestaan voor gebruikers om anderen
# te volgen.
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
    # Een lijst met alle bestaande studies waarbinnen de gebruiker betrokken is.
    studies = [study for study in Study.query.all() if current_user in study.linked_users]

    return render_template("current_studies.html", title='Current studies', studies=studies)


@bp.route('/standard_questions/<username>', methods=['GET', 'POST'])
@login_required
def standard_questions(username):
    user = User.query.filter_by(username=username).first_or_404()
    studies = Study.query.all()
    # Alle kernvariabelen welke binnen de applicatie standaard horen of de gebruiker heeft aangemaakt.
    corevariables = [core_variable for core_variable in CoreVariable.query.filter_by(user_id=current_user.id)] + \
                    [core_variable for core_variable in CoreVariable.query.filter_by(user_id=None)]
    # Een query met alle standaardvragen van de gebruiker.
    questions = StandardQuestion.query.filter_by(user_id=user.id)

    return render_template("standard_questions.html", title='New Study', user=user, studies=studies,
                           corevariables=corevariables,
                           questions=questions)


@bp.route('/standard_questions/new_question_user/<name_corevariable>/<username>', methods=['GET', 'POST'])
@login_required
def new_standard_question(name_corevariable, username):
    # De Form voor het aanmaken van een nieuwe standaardvraag.
    form = CreateNewQuestionUser()

    # Als de gebruiker aangeeft een nieuwe standaardvraag aangemaakt te hebben.
    if form.validate_on_submit():
        corevariable = CoreVariable.query.filter_by(name=name_corevariable).first_or_404()
        user = User.query.filter_by(username=username).first_or_404()
        new_question = StandardQuestion(question=form.name_question.data,
                                        user_id=user.id,
                                        corevariable_id=corevariable.id)
        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for("main.standard_questions", username=username))

    return render_template("new_standard_question.html", title="New Question", form=form)


@bp.route('/remove_standard_question/<id_question>', methods=['GET', 'POST'])
@login_required
def remove_standard_question(id_question):
    # Het verwijderen van de standaardvraag.
    StandardQuestion.query.filter_by(id=id_question).delete()
    db.session.commit()

    return redirect(url_for('main.standard_questions', username=current_user.username))


@bp.route('/standard_demographics/<username>', methods=['GET', 'POST'])
@login_required
def standard_demographics(username):
    user = User.query.filter_by(username=username).first_or_404()
    studies = Study.query.all()
    # Alle standaarddemografieken welke de gebruiker heeft aangemaakt.
    demographics = [demographic for demographic in StandardDemographic.query.filter_by(user_id=current_user.id)]

    return render_template("standard_demographics.html", title='Standard demographics', user=user, studies=studies,
                           demographics=demographics)


@bp.route('/standard_questions/new_question_user', methods=['GET', 'POST'])
@login_required
def new_standard_demographic():
    # De Form voor het aanmaken van een nieuwe standaarddemografiek.
    form = CreateNewDemographicForm()

    # Als de gebruiker aangeeft een nieuwe standaarddemografiek aangemaakt te hebben.
    if form.validate_on_submit():

        new_demographic = StandardDemographic(name=form.name_of_demographic.data,
                                              description=form.description_of_demographic.data,
                                              choices=form.choices_of_demographic.data,
                                              optional=form.optionality_of_demographic.data,
                                              questiontype_name=form.type_of_demographic.data,
                                              user_id=current_user.id)
        db.session.add(new_demographic)
        db.session.commit()

        return redirect(url_for("main.standard_demographics", username=current_user.username))

    return render_template("new_standard_demographic.html", title="New standard demographic", form=form)


@bp.route('/remove_standard_demographic/<id_demographic>', methods=['GET', 'POST'])
@login_required
def remove_standard_demographic(id_demographic):
    standard_question = StandardDemographic.query.filter_by(id=id_demographic).first()
    # Als de standaardvraag niet van de huidige gebruiker is aangeven dat de gebruiker niet geauthoriseerd is.
    if standard_question.user_id != current_user.id:
        return redirect(url_for('main.not_authorized'))

    # Het verwijderen van de standaarddemografiek.
    StandardDemographic.query.filter_by(id=id_demographic).delete()
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
    # Als de gebruiker nog niet in een sessie zit een nieuwe sessie aanmaken.
    if "user" not in session:
        session["user"] = str(uuid.uuid4())
        session["study"] = study_code

    # Als de gebruiker al in een sessie zit verwijzen naar de vragenlijst.
    if session["user"] in [case.session_id for case in Case.query.all()]:
        flash('You are currently already in a session. Complete the questionnaire.')  # return eerste blok vragenpagina
        return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

    # De Form om aangeven te starten met het onderzoek.
    form = GoToStartQuestionlist()
    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]

    # Als de gebruiker aangeeft door te willen gaan naar de start van de vragenlijst.
    if form.validate_on_submit():
        return redirect(url_for('main.start_questionlist', study_code=study_code))

    return render_template('intro_questionlist.html', title="Intro: {}".format(study.name), study=study,
                           study_code=study_code, form=form, demographics=demographics)


@bp.route('/d/e/start/<study_code>', methods=['GET', 'POST'])
def start_questionlist(study_code):
    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    # Een dictionary met de demografieken en een "return field" zodat de gebruiker alle demografieken kan invullen en
    # deze ook daadwerkelijk opgeslagen worden.
    demographics_dict = {}
    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]
    for demographic in demographics:
        demographics_dict[demographic.name] = demographic.return_field()
    form = DynamicTestForm(demographics_dict)

    # Als de gebruiker aangeeft de demografieken ingevuld te hebben.
    if form.validate_on_submit():
        if session["user"] in [case.session_id for case in Case.query.all()] and session["study"] == study_code:
            flash('You are currently already in a session. Complete the questionnaire.')
            return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

        study = Study.query.filter_by(code=study_code).first()
        questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
        # Het toevoegen van een case aan de database.
        case = Case(session_id=session["user"], questionnaire_id=questionnaire.id)
        db.session.add(case)
        db.session.commit()

        # De antwoorden op de demografieken worden nog niet opgeslagen in de database, maar wel in de sessie.
        session["demographic_answers"] = []
        for (demographic, answer) in zip([demographic for demographic in demographics], form.data.values()):
            demographic_answer = DemographicAnswer(answer=answer, demographic_id=demographic.id,
                                                   case_id=Case.query.filter_by(session_id=session["user"]).first().id)
            session["demographic_answers"].append(demographic_answer)

        # Een dictionary met een numerieke key (0 tot en met zoveel) en de vragengroep (questiongroup_dict).
        questiongroup_dict = {}
        questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]
        keys = range(len(questiongroups))
        for i in keys:
            questiongroup_dict[i] = questiongroups[i]

        # Evenals de demografische antwoorden worden de antwoorden op de vragen nog niet opgeslagen in de database, maar
        # wel in de sessie. De eerste twee sessiedata hieronder zijn om de vragenlijst goed te renderen (de eerste om
        # de vragenlijst op te delen tussen de vragengroepen, de tweede om te gaan naar het eindscherm zodra de laatste
        # is ingevuld).
        session["questionlist_questiongroups"] = questiongroup_dict
        session["questionlist_maxamount"] = QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id).count()
        session["answers"] = []

        return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

    return render_template('start_questionlist.html', title="Start: {}".format(study.name), study=study, form=form)


@bp.route('/c/e/<study_code>/<questionlist_number>', methods=['GET', 'POST'])
def questionlist(study_code, questionlist_number):
    # Als de vragengroepnummer groter is dan de hoeveelheid vragengroepen wordt de gebruiker verwezen naar het einde.
    if int(questionlist_number) >= session['questionlist_maxamount']:
        return redirect(url_for('main.ending_questionlist', study_code=study_code))

    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    questionlist = session["questionlist_questiongroups"][int(questionlist_number)]
    questions = [question for question in Question.query.filter_by(questiongroup_id=questionlist.id)]

    # Een dictionary met de vraag als key en een bijbehorende Field om in te vullen als waarde (questions_dict).
    questions_dict = {}
    for question in questions:
        questions_dict[question.question] = RadioField(question.question,
                                                       choices=[number for number in range(1, questionnaire.scale + 1)])
    form = DynamicTestForm(questions_dict)

    # De volgende vragengroepnummer voor de verwijzing zodra de gebruiker dit gedeelte van de vragenlijst heeft ingevuld
    next_questionlist_number = int(questionlist_number) + 1

    # Als de gebruiker aangeeft dit gedeelte van de vragenlijst ingevuld te hebben.
    if form.validate_on_submit():
        for (question, value) in zip([question for question in questions], form.data.values()):
            # Deze "isinstance" regel wordt opgeroepen om enkele waarden welke toegevoegd werden en niet binnen de
            # antwoorden horen weg te werken. Dit kan gezien worden als een makkelijke work-around.
            if isinstance(value, str) and len(value) < 4:
                # Als een antwoord op de vraag al gegeven is binnen de sessie.
                if question.id in [answer.question_id for answer in session["answers"]]:
                    for answer in session["answers"]:
                        # Voor de vraag die inderdaad al beantwoord is.
                        if answer.question_id == question.id:
                            # Als de vraag met "reversed_score" werkt de gegeven score omdraaien.
                            if question.reversed_score:
                                answer.score = reverse_value(value, questionnaire.scale)
                            else:
                                answer.score = value
                # Als nog geen antwoord op de vraag gegeven is binnen de sessie.
                else:
                    # Als de vraag met "reversed_score" werkt de gegeven score omdraaien. Het antwoord sowieso toevoegen
                    # aan de sessie.
                    if question.reversed_score:
                        answer = Answer(score=reverse_value(value, questionnaire.scale), question_id=question.id,
                                        case_id=Case.query.filter_by(session_id=session["user"]).first().id)
                        session["answers"].append(answer)
                    else:
                        answer = Answer(score=value, question_id=question.id,
                                        case_id=Case.query.filter_by(session_id=session["user"]).first().id)
                        session["answers"].append(answer)
        # Naar het volgende onderdeel van de vragenlijst gaan.
        return redirect(
            url_for('main.questionlist', study_code=study_code, questionlist_number=next_questionlist_number))

    return render_template('questionlist.html',
                           title="Questionlist {}: {}".format(str(questionlist_number), study.name),
                           study=study, questionlist_number=questionlist_number, questions=questions,
                           questionlist=questionlist, next_questionlist_number=next_questionlist_number, form=form)


@bp.route('/g/e/<study_code>', methods=['GET', 'POST'])
def ending_questionlist(study_code):
    study = Study.query.filter_by(code=study_code).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    total_question_number = 0
    for questiongroup in QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id):
        total_question_number += Question.query.filter_by(questiongroup_id=questiongroup.id).count()
    # Voor het geval de gebruiker probeert naar het einde te gaan zonder dat alle vragen zijn beantwoord.
    if len(session["answers"]) < total_question_number:
        flash('You have not answered all of the questions yet. Finish the questions.')
        return redirect(url_for('main.questionlist', study_code=study_code, questionlist_number=0))

    # De Form voor het aangeven dat de gebruiker inderdaad klaar is met de vragenlijst.
    form = EmptyForm()

    # Als de gebruiker aangeeft klaar te zijn met de vragenlijst.
    if form.validate_on_submit():
        # Het opslaan van de antwoorden op de vragen in de database.
        for answer in session["answers"]:
            db.session.add(answer)
            db.session.commit()
        # Het opslaan van de demografische antwoorden in de database.
        for answer in session["demographic_answers"]:
            db.session.add(answer)
            db.session.commit()
        # Aangeven dat de vragenlijst voltooid is door de gebruiker/specifieke case.
        Case.query.filter_by(session_id=session["user"]).first().completed = True
        db.session.commit()
        session.clear()
        return "Thank you for participating."
    return render_template('ending_questionlist.html', title="Ending Questionnaire", form=form)
