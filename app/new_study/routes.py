from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
import numpy as np
import pandas as pd
import plspm.config as c
import json
from plspm.plspm import Plspm
from plspm.scheme import Scheme
from plspm.mode import Mode
from app import db
from app.models import User, Study, UTAUTmodel, CoreVariable, Relation, Questionnaire, Question, StandardQuestion, \
    QuestionGroup, Demographic, StandardDemographic, Case, DemographicAnswer, Answer
from app.new_study import bp
from app.new_study.forms import CreateNewStudyForm, CreateNewCoreVariableForm, CreateNewRelationForm, \
    CreateNewQuestion, ChooseNewModel, AddCoreVariable, EditStudyForm, AddDemographic, AddUserForm, ScaleForm, \
    CreateNewDemographicForm
from app.new_study.functions import variance, cronbachs_alpha, composite_reliability, average_variance_extracted, \
    covariance, pearson_correlation, correlation_matrix, heterotrait_monotrait, htmt_matrix, outer_vif_values_dict
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant


#############################################################################################################
#                                        De studie opzetten
#############################################################################################################


@bp.route('/new_study', methods=['GET', 'POST'])
@login_required
def new_study():
    # De Form voor het aanmaken van een nieuw onderzoek.
    form = CreateNewStudyForm()

    # Als de gebruiker aangeeft een nieuw onderzoek aan te willen maken
    if form.validate_on_submit():
        # Ter automatisme wordt het UTAUT-model als standaardonderzoeksmodel gebruikt voor nieuwe onderzoeken.

        # Een nieuw onderzoeksmodel wordt aangemaakt binnen de database.
        # new_model is een "UTAUTmodel"-object (UTAUTmodel is een tabel binnen de database) met de naam "UTAUT" ("name"
        # is één van de eigenschappen die ingegeven kan worden). Vervolgens wordt dit model toegevoegd (db.session.add)
        # en opgeslagen binnen de database (db.session.commit).
        new_model = UTAUTmodel(name="UTAUT")
        db.session.add(new_model)
        db.session.commit()

        # De kernvariabelen met de gegeven afkortingen worden toegevoegd aan het onderzoeksmodel.
        for abbreviation in ["PE", "EE", "SI", "FC", "BI", "UB"]:
            # "Query" wordt gebruikt om objecten binnen de tabel (CoreVariable) te selecteren. filter_by is een manier
            # om te filteren op welke objecten geselecteerd worden. In dit geval dient de "abbreviation" (afkorting)
            # gelijk te zijn aan, in de eerste instantie van de for loop, "PE". first() is een manier om deze
            # daadwerkelijk de eerste instantie van de query (van alle objecten die "PE" als afkorting hebben) te
            # returnen.
            corevariable = CoreVariable.query.filter_by(abbreviation=abbreviation).first()
            # De relevante kernvariabele wordt gelinkt aan het model. Zie "models.py" om de wijze waarop "linken" werkt
            # te bestuderen.
            corevariable.link(new_model)

        # De sublisten van hieronder worden omgezet in verschillende relaties.
        for sublist in [["PE", "BI"], ["EE", "BI"], ["SI", "BI"], ["FC", "UB"], ["BI", "UB"]]:
            # Door het gebruik van "id" wordt al gelijk de ID van de kernvariabele geselecteerd die als eerste
            # gereturned is door de query.
            # De ID van de beïnvloedende kernvariabele bepalen.
            id_influencer = CoreVariable.query.filter_by(
                abbreviation=sublist[0]).first().id
            # De ID van de beïnvloede kernvariabele bepalen.
            id_influenced = CoreVariable.query.filter_by(
                abbreviation=sublist[1]).first().id

            # Een nieuwe relatie wordt aangemaakt binnen het gegeven onderzoeksmodel tussen de kernvariabelen.
            newrelation = Relation(model_id=new_model.id,
                                   influencer_id=id_influencer,
                                   influenced_id=id_influenced)
            db.session.add(newrelation)
            db.session.commit()

        # Een nieuw onderzoek wordt opgezet.
        new_study = Study(name=form.name_of_study.data, description=form.description_of_study.data,
                          technology=form.technology_of_study.data, model_id=new_model.id)
        # Een unieke code wordt gegeven aan het onderzoek (gebruikmakend van UUID4).
        new_study.create_code()
        db.session.add(new_study)
        db.session.commit()

        # De huidige gebruiker wordt gelinkt aan het onderzoek.
        current_user.link(new_study)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=new_study.code))
    return render_template("new_study/new_study.html", title='New Study', form=form)


@bp.route('/edit_study/<study_code>', methods=['GET', 'POST'])
@login_required
def edit_study(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De Form voor het aanpassen van het onderzoek.
    form = EditStudyForm(study.name, study.description, study.technology)

    # Als de gebruiker aangeeft de onderzoek te willen aanpassen met de gegeven gegevens.
    if form.validate_on_submit():
        # De gegevens van de studie worden aangepast naar de ingegeven data binnen de Form.
        study.name = form.name_of_study.data
        study.description = form.description_of_study.data
        study.technology = form.technology_of_study.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('new_study.utaut', study_code=study.code))
    # Als niks is ingegeven binnen de Form worden geen aanpassingen gemaakt (en dus gebruikgemaakt van de eigen
    # onderzoeksgegevens.
    elif request.method == 'GET':
        form.name_of_study.data = study.name
        form.description_of_study.data = study.description
        form.technology_of_study.data = study.technology
    return render_template('new_study/edit_study.html', title='Edit Profile',
                           form=form, study=study)


# Deze pagina is nog niet gerealiseerd.
@bp.route('/add_user/<study_code>', methods=['GET', 'POST'])
@login_required
def add_user(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De Form voor het toevoegen van een nieuwe gebruiker aan het onderzoek.
    form = AddUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name_user.data).first()
        user.link(study)
        db.session.commit()

        flash('Your changes have been saved.')
        return redirect(url_for('new_study.edit_study', study_code=study_code))

    return render_template('new_study/add_user.html', title='Edit Profile',
                           form=form, study=study)


#############################################################################################################
#                                      Onderzoeksmodel opstellen
#############################################################################################################

@bp.route('/utaut/<study_code>', methods=['GET', 'POST'])
@login_required
def utaut(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    core_variables = [corevariable for corevariable in model.linked_corevariables]
    relations = [relation for relation in Relation.query.filter_by(model_id=model.id)]

    # Het selectiemenu van bestaande kernvariabelen welke toegevoegd kunnen worden aan het onderzoeksmodel.
    form_add_variable = AddCoreVariable()
    form_add_variable.add_variable.choices = [(core_variable.id, core_variable.name) for core_variable in
                                              CoreVariable.query.filter_by(user_id=current_user.id)] + \
                                             [(core_variable.id, core_variable.name) for core_variable in
                                              CoreVariable.query.filter_by(user_id=None)]

    # Als de gebruiker een kernvariabele uit het selectiemenu aangeeft te willen toevoegen.
    if form_add_variable.validate_on_submit():
        core_variable = CoreVariable.query.filter_by(id=form_add_variable.add_variable.data).first()
        core_variable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=study_code))

    return render_template("new_study/utaut.html", title='UTAUT', study=study, model=model,
                           core_variables=core_variables, relations=relations, form_add_variable=form_add_variable)


@bp.route('/utaut/new_core_variable/<study_code>', methods=['GET', 'POST'])
@login_required
def new_core_variable(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    study = Study.query.filter_by(code=study_code).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De Form voor het aanmaken van een nieuwe kernvariabele.
    form = CreateNewCoreVariableForm()

    # Als de gebruiker aangeeft een nieuwe kernvariabele te willen aanmaken.
    if form.validate_on_submit():
        # De kernvariabele toegevoegd aan de database.
        new_corevariable = CoreVariable(name=form.name_corevariable.data,
                                        abbreviation=form.abbreviation_corevariable.data,
                                        description=form.description_corevariable.data,
                                        user_id=current_user.id)
        db.session.add(new_corevariable)
        db.session.commit()

        # De kernvariabele wordt binnen het onderzoeksmodel geplaatst.
        model = UTAUTmodel.query.filter_by(id=study.model_id).first()
        new_corevariable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=study_code))

    return render_template("new_study/new_corevariable.html", title='New Core Variable', form=form)


@bp.route('/remove_core_variable/<study_code>/<corevariable_id>', methods=['GET', 'POST'])
@login_required
def remove_core_variable(study_code, corevariable_id):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()

    # De kernvariabele uit het onderzoeksmodel halen en alle bijbehorende relaties verwijderen.
    corevariable.unlink(model)
    db.session.commit()
    Relation.query.filter_by(influencer_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()
    Relation.query.filter_by(influenced_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()

    # Als de kernvariabele al een vragenlijstgroep had binnen de vragenlijst deze en de bijbehorende vragen verwijderen.
    if questionnaire:
        questiongroup = QuestionGroup.query.filter_by(title=corevariable.name,
                                                      questionnaire_id=questionnaire.id).first()
        Question.query.filter_by(questiongroup_id=questiongroup.id).delete()
        db.session.commit()
        QuestionGroup.query.filter_by(title=corevariable.name, questionnaire_id=questionnaire.id).delete()
        db.session.commit()

    return redirect(url_for('new_study.utaut', study_code=study_code))


@bp.route('/utaut/new_relation/<study_code>', methods=['GET', 'POST'])
@login_required
def new_relation(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De Form voor het aanmaken van een nieuwe relatie.
    form = CreateNewRelationForm()

    # Als de gebruiker aangeeft een nieuwe relatie aan te willen maken.
    if form.validate_on_submit():
        model = UTAUTmodel.query.filter_by(id=study.model_id).first()

        # De ID van de beïnvloedende kernvariabele bepalen.
        id_influencer = CoreVariable.query.filter_by(
            abbreviation=form.abbreviation_influencer.data).first().id
        # De ID van de beïnvloede kernvariabele bepalen.
        id_influenced = CoreVariable.query.filter_by(
            abbreviation=form.abbreviation_influenced.data).first().id

        # De relatie aanmaken tussen de twee relevante kernvariabelen.
        newrelation = Relation(model_id=model.id,
                               influencer_id=id_influencer,
                               influenced_id=id_influenced)
        db.session.add(newrelation)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=study_code))

    return render_template("new_study/new_relation.html", title='New Relation', form=form)


@bp.route('/remove_relation/<study_code>/<id_relation>', methods=['GET', 'POST'])
@login_required
def remove_relation(study_code, id_relation):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # Het verwijderen van de relevante relatie.
    Relation.query.filter_by(id=id_relation).delete()
    db.session.commit()

    return redirect(url_for('new_study.utaut', study_code=study_code))


#############################################################################################################
#                                        Vragenlijst opstellen
#############################################################################################################


@bp.route('/pre_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def pre_questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # Voor het geval geen vragenlijst nog is opgesteld een vragenlijst aanmaken voor het onderzoek.
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    if Questionnaire.query.filter_by(study_id=study.id).first() is None:
        newquestionnaire = Questionnaire(study_id=study.id)
        db.session.add(newquestionnaire)
        db.session.commit()

        # Vragenlijstgroepen aanmaken per kernvariabele.
        for corevariable in model.linked_corevariables:
            questiongroup = QuestionGroup(title=corevariable.name, group_type="likert",
                                          questionnaire_id=newquestionnaire.id,
                                          corevariable_id=corevariable.id)
            db.session.add(questiongroup)
            db.session.commit()

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    # De Form voor de schaal voor gebruikers om in te vullen
    form = ScaleForm(questionnaire.scale)

    # Bij ingeving van de schaal de schaal van de vragenlijst omzetten.
    if form.validate_on_submit():
        questionnaire.scale = form.scale.data
        db.session.commit()
        return redirect(url_for('new_study.questionnaire', study_code=study_code))

    return render_template("new_study/pre_questionnaire.html", title='Pre-questionnaire', study=study, model=model,
                           form=form)


@bp.route('/questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    # Voor het geval nieuwe kernvariabelen zijn toegevoegd aan het onderzoeksmodel nieuwe vragenlijstgroepen aanmaken.
    for core_variable in model.linked_corevariables:
        if core_variable.id not in [questiongroup.corevariable_id for questiongroup
                                    in QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]:
            questiongroup = QuestionGroup(title=core_variable.name, group_type="likert",
                                          questionnaire_id=questionnaire.id,
                                          corevariable_id=core_variable.id)
            db.session.add(questiongroup)
            db.session.commit()

    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]

    # Een dictionary met sublijsten van alle vragen per vragenlijstgroep/kernvariabele (questiongroups_questions)
    # en de opzet ervan
    questions = []
    for questiongroup in questiongroups:
        questions.append(
            [question for question in
             Question.query.filter_by(questiongroup_id=questiongroup.id).all()])
    questiongroups_questions = dict(zip(questiongroups, questions))

    # Een lijst met de demographics die bij het onderzoek horen.
    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]

    return render_template("new_study/questionnaire.html", title='Questionnaire', study=study, model=model,
                           questiongroups=questiongroups, questionnaire=questionnaire,
                           questiongroups_questions=questiongroups_questions, demographics=demographics)


@bp.route('/questionnaire/switch_reversed_score/<study_code>/<name_question>', methods=['GET', 'POST'])
@login_required
def switch_reversed_score(study_code, name_question):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De reversed_score aan- of uitzetten voor de vraag afhankelijk wat de huidige stand is.
    question = Question.query.filter_by(question=name_question).first()
    if question.reversed_score:
        question.reversed_score = False
        db.session.commit()
    else:
        question.reversed_score = True
        db.session.commit()
    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/use_standard_questions_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def use_standard_questions_questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    study = Study.query.filter_by(code=study_code).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    # Een lijst met alle standaardvragen van de gebruiker
    standard_questions = [standard_question for standard_question in StandardQuestion.query.filter_by(user_id=user.id)]
    for standard_question in standard_questions:
        # De "(...)" vervangen door de voor het onderzoek relevante technologie
        replaced_name_question = standard_question.question.replace('(...)', study.technology)
        replaced_name_question = replaced_name_question.replace('(…)', study.technology)

        # De bijbehorende vragenlijstgroep van de standaardvraag
        corresponding_questiongroup = QuestionGroup.query.filter_by(
            corevariable_id=standard_question.corevariable_id, questionnaire_id=questionnaire.id).first()

        corevariable = CoreVariable.query.filter_by(name=corresponding_questiongroup.title,
                                                    user_id=current_user.id).first()

        # Als de kernvariabele niet aangemaakt is door de huidige gebruiker (dan hoort deze automatisch binnen het
        # programma te horen en dus geen user_id te hebben.
        if corevariable is None:
            corevariable = CoreVariable.query.filter_by(name=corresponding_questiongroup.title, user_id=None).first()

        # De toevoeging van de vraag aan de vragenlijst.
        if corevariable is not None:
            abbreviation_corevariable = corevariable.abbreviation
            # De code voor de vraag (de kernvariabele plus een cijfer, zoals "PE3")
            new_code = abbreviation_corevariable + str(len([question for question in
                                                            Question.query.filter_by(
                                                                questiongroup_id=corresponding_questiongroup.id)]) + 1)
            newquestion = Question(question=replaced_name_question,
                                   questiongroup_id=corresponding_questiongroup.id,
                                   question_code=new_code)
            db.session.add(newquestion)
            db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/use_standard_demographics_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def use_standard_demographics_questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    study = Study.query.filter_by(code=study_code).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic.name for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]

    # Alle standaarddemografieken van de gebruiker.
    standard_demographics = [standard_demographic for standard_demographic in
                             StandardDemographic.query.filter_by(user_id=user.id)]

    # Iedere standaarddemografiek toevoegen aan het onderzoek.
    for standard_demographic in standard_demographics:
        new_demographic = Demographic(name=standard_demographic.name,
                                      description=standard_demographic.description,
                                      choices=standard_demographic.choices,
                                      optional=standard_demographic.optional,
                                      questiontype_name=standard_demographic.questiontype_name,
                                      questionnaire_id=questionnaire.id)
        # Als de demografiek nog niet binnen het onderzoek is (als dit wel het geval is hoort deze niet toegevoegd te
        # worden.
        if new_demographic.name not in demographics:
            db.session.add(new_demographic)
            db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/new_question/<name_questiongroup>/<study_code>', methods=['GET', 'POST'])
@login_required
def new_question(name_questiongroup, study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # De Form voor het aanmaken van een nieuwe vraag.
    form = CreateNewQuestion()

    # Als de gebruiker aangeeft een nieuwe vraag aan te maken met de gegeven gegevens.
    if form.validate_on_submit():
        questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
        questiongroup = QuestionGroup.query.filter_by(title=name_questiongroup,
                                                      questionnaire_id=questionnaire.id).first()

        # De bijbehorende kernvariabele verkrijgen voor het bepalen van de afkorting van de correcte variabele.
        corevariable = CoreVariable.query.filter_by(name=questiongroup.title, user_id=current_user.id).first()
        if corevariable is None:
            corevariable = CoreVariable.query.filter_by(name=questiongroup.title, user_id=None).first()

        abbreviation_corevariable = corevariable.abbreviation

        # De code voor de vraag (de kernvariabele plus een cijfer, zoals "PE3")
        new_code = abbreviation_corevariable + str(len([question for question in
                                                        Question.query.filter_by(
                                                            questiongroup_id=questiongroup.id)]) + 1)

        # Het aanmaken van een nieuwe vraag in de database.
        new_question = Question(question=form.name_question.data,
                                questiongroup_id=questiongroup.id,
                                question_code=new_code)
        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for("new_study.questionnaire", study_code=study_code))

    return render_template("new_study/new_question.html", title="New Question", form=form)


@bp.route('/remove_question/<study_code>/<name_question>', methods=['GET', 'POST'])
@login_required
def remove_question(study_code, name_question):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # Het verwijderen van de vraag uit de database.
    Question.query.filter_by(question=name_question).delete()
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/new_demographic/<study_code>', methods=['GET', 'POST'])
@login_required
def new_demographic(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    # De Form voor het aanmaken van een nieuwe demografiek.
    form = CreateNewDemographicForm()

    # Als de gebruiker aangeeft een nieuwe demografiek aan te maken met de gegeven gegevens.
    if form.validate_on_submit():
        new_demographic = Demographic(name=form.name_of_demographic.data,
                                      description=form.description_of_demographic.data,
                                      choices=form.choices_of_demographic.data,
                                      optional=form.optionality_of_demographic.data,
                                      questiontype_name=form.type_of_demographic.data,
                                      questionnaire_id=questionnaire.id)
        db.session.add(new_demographic)
        db.session.commit()

        return redirect(url_for("new_study.questionnaire", study_code=study_code))

    return render_template("new_study/new_demographic.html", title="New Question", form=form)


@bp.route('/remove_demographic/<study_code>/<id_demographic>', methods=['GET', 'POST'])
@login_required
def remove_demographic(study_code, id_demographic):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # Het verwijderen van de demografiek uit de database.
    Demographic.query.filter_by(id=id_demographic).delete()
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study.code))


@bp.route('/check_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def check_questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]

    # Bepalen of alle vragenlijstgroepen tenminste één vraag hebben. Zo niet, de Flash geven en terugkeren.
    for questiongroup in questiongroups:
        if Question.query.filter_by(questiongroup_id=questiongroup.id).count() == 0:
            flash('One or more of the core variables does not have questions yet. Please add at least one question to '
                  'each core variable.')
            return redirect(url_for('new_study.questionnaire', study_code=study.code))

    return redirect(url_for('new_study.start_study', study_code=study.code))


#############################################################################################################
#                                          Start onderzoek
#############################################################################################################

@bp.route('/start_study/<study_code>', methods=['GET', 'POST'])
@login_required
def start_study(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    # Omzetting studie van stage_1 (opstellen van het onderzoek) naar stage_2 (het onderzoek is gaande)
    study.stage_1 = False
    study.stage_2 = True
    db.session.commit()

    return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))


@bp.route('/study_underway/<name_study>/<study_code>', methods=['GET', 'POST'])
@login_required
def study_underway(name_study, study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    # Checken hoe ver de studie is
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))
    # De link naar de vragenlijst
    link = '127.0.0.1:5000/d/e/{}'.format(study.code)

    return render_template('new_study/study_underway.html', title="Underway: {}".format(name_study), study=study,
                           link=link, questionnaire=questionnaire)


@bp.route('/end_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def end_questionnaire(study_code):
    # Checken of gebruiker tot betrokken onderzoekers hoort
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # Omzetting studie van stage_2 (het onderzoek is gaande) naar stage_3 (de data-analyse)
    study.stage_2 = False
    study.stage_3 = True
    db.session.commit()

    return redirect(url_for('new_study.summary_results', study_code=study_code))


#############################################################################################################
#                                     Data Analyse en visualisatie
#############################################################################################################

@bp.route('/summary_results/<study_code>', methods=['GET', 'POST'])
@login_required
def summary_results(study_code):
    study = Study.query.filter_by(code=study_code).first()
    # Checken of gebruiker tot betrokken onderzoekers hoort
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]
    total_cases = [case for case in Case.query.filter_by(questionnaire_id=questionnaire.id)]

    # Samenvatting van de demografische resultaten

    # Een lijst met alle case-id's en de opzet ervan.
    cases = []
    for case in total_cases:
        for i in range(len(demographics)):
            cases.append(case.id)

    # Namen van de demografieken en de opzet ervan
    demos = []
    for case in total_cases:
        for demographic in demographics:
            demos.append(demographic.name)

    # Dictionary met de Case-id's als keys en de gegeven demografische antwoorden als waarden en de opzet ervan
    dct_demographics = {}
    for case in cases:
        dct_demographics[case] = []
    for (case_id, demo_name) in zip(cases, demos):
        demo = Demographic.query.filter_by(name=demo_name).first()
        answer = DemographicAnswer.query.filter_by(case_id=case_id, demographic_id=demo.id).first()
        if answer is not None:
            dct_demographics[case_id].append(answer.answer)
        else:
            dct_demographics[case_id].append(None)

    # Samenvatting van de vragenlijstresultaten voor iedere case

    # Alle vragengroepen binnen de vragenlijst
    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]

    # Een lijst met de vragen en de opzet ervan
    questions = []
    for questiongroup in questiongroups:
        list_of_questions = [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]
        for question in list_of_questions:
            questions.append(question)

    # Een lijst met de Case-id's
    cases = []
    for case in total_cases:
        for i in range(len(questions)):
            cases.append(case.id)

    # Een lijst met de vragen in stringvorm en de opzet ervan
    quests = []
    for case in total_cases:
        for question in questions:
            quests.append(question.question)

    # Een dictionary met alle cases en de bijbehorende antwoorden op de vragen en de opzet ervan
    dct_answers = {}
    for case in cases:
        dct_answers[case] = []
    for (case_id, quest_name) in zip(cases, quests):
        for questiongroup in questiongroups:
            quest = Question.query.filter_by(question=quest_name, questiongroup_id=questiongroup.id).first()
            if quest is not None:
                answer = Answer.query.filter_by(question_id=quest.id, case_id=case_id).first()
                if answer is not None:
                    dct_answers[case_id].append(answer.score)
                else:
                    dct_answers[case_id].append(None)

    # Samenvatting van de gemiddeldes en standaarddeviaties voor iedere vraag

    # Het creëren van een dictionary met de vragen en een lijst waar de gemiddelden en standaarddeviaties in komen
    dct_questions = {}
    for questiongroup in questiongroups:
        for question in [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]:
            dct_questions[question] = []

    #Voor iedere vraag in de vragenlijst
    for question in dct_questions:
        # Een lijst met de scores van de specifieke vraag
        answer_scores = []
        for answer in [answer for answer in Answer.query.filter_by(question_id=question.id)]:
            answer_scores.append(int(answer.score))
        array = np.array(answer_scores)
        # Het toevoegen het gemiddelde en de standaarddeviatie van de specifieke vraag
        dct_questions[question].extend([round(np.average(array), 2), round(np.std(array), 2)])

    return render_template('new_study/summary_results.html', study_code=study_code, demographics=demographics,
                           cases=cases, dct_demographics=dct_demographics, dct_answers=dct_answers, questions=questions,
                           dct_questions=dct_questions, study=study)


@bp.route('/data_analysis/<study_code>', methods=['GET', 'POST'])
@login_required
def data_analysis(study_code):
    study = Study.query.filter_by(code=study_code).first()

    # Checken of gebruiker tot betrokken onderzoekers hoort
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    corevariables = [corevariable for corevariable in model.linked_corevariables]

    # Het opzetten van de dataframe (gebruik van plspm package en pd.dataframe met de vragenlijstresultaten)
    list_of_questions = []
    list_of_answers = []
    questiongroups = [questiongroup for questiongroup in
                      QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]
    for questiongroup in questiongroups:
        questions = [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]
        for question in questions:
            list_of_questions.append(question.question_code)
            answers_question = []
            for answer in [answer for answer in Answer.query.filter_by(question_id=question.id)]:
                answers_question.append(answer.score)
            list_of_answers.append(answers_question)

    df = pd.DataFrame(list_of_answers).transpose()
    df.columns = list_of_questions

    structure = c.Structure()

    for corevariable in corevariables:
        influenced_variables = []
        for relation in [relation for relation in Relation.query.filter_by(model_id=model.id)]:
            if relation.influencer_id == corevariable.id:
                influenced = CoreVariable.query.filter_by(id=relation.influenced_id).first()
                influenced_variables.append(influenced.abbreviation)
        if len(influenced_variables) > 0:
            structure.add_path([corevariable.abbreviation], influenced_variables)

    config = c.Config(structure.path(), scaled=False)

    for corevariable in corevariables:
        config.add_lv_with_columns_named(corevariable.abbreviation, Mode.A, df, corevariable.abbreviation)

    plspm_calc = Plspm(df, config, Scheme.CENTROID)
    model1 = plspm_calc.outer_model()

    # Creëert dictionary met alleen loadings van latente variabele
    # KIJKEN NAAR CODEFORMAT
    loadings_dct = pd.DataFrame(model1['loading']).to_dict('dict')['loading']
    for code in loadings_dct:
        loadings_dct[code] = round(float(loadings_dct[code]), 4)
        possible_questions = Question.query.filter_by(question_code=code)
        actual_question = None
        for question in possible_questions:
            questiongroup = QuestionGroup.query.filter_by(id=question.questiongroup_id).first()
            if questiongroup.questionnaire_id == questionnaire.id:
                actual_question = Question.query.filter_by(questiongroup_id=questiongroup.id, question_code=code).first()
                break
        loadings_dct[code] = [actual_question.question, loadings_dct[code]]

    # Alle data voor AVE, Cronbachs Alpha en Composite Reliability wordt hier opgesteld. Modules bovenaan geïmporteerd.
    data_construct_validity = {}
    for corevariable in corevariables:
        data_construct_validity[corevariable] = [round(cronbachs_alpha(corevariable, df), 4),
                                                 round(composite_reliability(corevariable, df, config, Scheme.CENTROID),
                                                       4),
                                                 round(average_variance_extracted(corevariable, df, config,
                                                                                  Scheme.CENTROID), 4)]

    # Een matrix van Heterotrait-Monotrait Ratio wordt hier beschikbaar gemaakt (module "htmt_matrix" staat bovenaan
    # verwezen.
    data_htmt = htmt_matrix(df, model)
    amount_of_variables = len(corevariables)

    # Buitenste VIF-waarden worden hier beschikbaar gemaakt in een dictionary onder "data_outer_vif". Module bovenaan
    # geïmporteerd.
    data_outer_vif = outer_vif_values_dict(df, questionnaire)

    return render_template('new_study/data_analysis.html', study_code=study_code,
                           data_construct_validity=data_construct_validity, data_outer_vif=data_outer_vif,
                           data_htmt=data_htmt, amount_of_variables=amount_of_variables, study=study,
                           loadings_dct=loadings_dct)


@bp.route('/data_analysis/corevariable_analysis/<study_code>/<corevariable_id>', methods=['GET', 'POST'])
@login_required
def corevariable_analysis(study_code, corevariable_id):
    study = Study.query.filter_by(code=study_code).first()

    # Checken of gebruiker tot betrokken onderzoekers hoort
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # Checken hoe ver de studie is
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()
    corevariables = [corevariable for corevariable in model.linked_corevariables]
    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]

    # De lengte van de afkorting van de kernvariabele voor het geval bepaald moet worden of een specifieke afkorting
    # die van de relevante kernvariabele is.
    length_abbreviation = len(corevariable.abbreviation)

    # De items/vragen (de code specifiek gezegd) die horen bij de kernvariabele
    items_lv = []
    for questiongroup in questiongroups:
        for question in Question.query.filter_by(questiongroup_id=questiongroup.id):
            if question.question_code[:length_abbreviation] == corevariable.abbreviation:
                items_lv.append(question.question_code)
    length_items_lv = len(items_lv)

    # Het opzetten van de dataframe (gebruik van plspm package en pd.dataframe met de vragenlijstresultaten)
    list_of_questions = []
    list_of_answers = []

    for questiongroup in questiongroups:
        questions = [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]
        for question in questions:
            list_of_questions.append(question.question_code)
            answers_question = []
            for answer in [answer for answer in Answer.query.filter_by(question_id=question.id)]:
                answers_question.append(answer.score)
            list_of_answers.append(answers_question)
    df = pd.DataFrame(list_of_answers).transpose()
    df.columns = list_of_questions

    structure = c.Structure()
    for corevariable in corevariables:
        influenced_variables = []
        for relation in [relation for relation in Relation.query.filter_by(model_id=model.id)]:
            if relation.influencer_id == corevariable.id:
                influenced = CoreVariable.query.filter_by(id=relation.influenced_id).first()
                influenced_variables.append(influenced.abbreviation)
        if len(influenced_variables) > 0:
            structure.add_path([corevariable.abbreviation], influenced_variables)

    config = c.Config(structure.path(), scaled=False)

    for corevariable in corevariables:
        config.add_lv_with_columns_named(corevariable.abbreviation, Mode.A, df, corevariable.abbreviation)

    plspm_calc = Plspm(df, config, Scheme.CENTROID)
    model1 = plspm_calc.outer_model()

    # De AVE, Cronbach's Alpha, Composite Reliability voor de fullscreen grafieken (met alle kernvariabelen erin).
    corevariable_names_js_all = [corevariable for corevariable in model.linked_corevariables]
    corevariable_ave_js_all = [round(average_variance_extracted(corevariable, df, config, Scheme.CENTROID), 4) for
                               corevariable in corevariables]
    corevariable_ca_js_all = [round(cronbachs_alpha(corevariable, df), 4) for corevariable in corevariables]
    corevariable_cr_js_all = [round(composite_reliability(corevariable, df, config, Scheme.CENTROID), 4) for
                              corevariable
                              in corevariables]

    # De AVE, Cronbach's Alpha, Composite Reliability, ladingen, VIF-waarden en HTMT-ratios voor de kleinere grafieken
    # (voor AVE, CA, CR en HTMT worden de twee/drie dichtstbijzijnde kernvariabelen gebruikt).

    # De indexes van de eerste dichtstbijzijnde kernvariabele, de specifieke kernvariabele en de tweede dichtstbijzijnde
    # kernvariabele respectievelijk.
    indexes_corevariables = []
    for corevariable in corevariables:
        if corevariable.id == int(corevariable_id):
            if corevariables.index(corevariable) == 0:
                indexes_corevariables = [0, 1, 2]
            elif corevariables.index(corevariable) == len(corevariables) - 1:
                indexes_corevariables = [len(corevariables) - 3, len(corevariables) - 2, len(corevariables) - 1]
            else:
                indexes_corevariables = [corevariables.index(corevariable) - 1, corevariables.index(corevariable),
                                         corevariables.index(corevariable) + 1]

    # Namen van de eerste dichtstbijzijnde kernvariabele, de specifieke kernvariabele en de tweede dichtstbijzijnde
    # kernvariabele respectievelijk.
    corevariable_names_js = [corevariable for corevariable in
                             [corevariables[indexes_corevariables[0]], corevariables[indexes_corevariables[1]],
                              corevariables[indexes_corevariables[2]]]]
    # AVE-lijst
    corevariable_ave_js = [round(average_variance_extracted(corevariable, df, config, Scheme.CENTROID), 4) for
                           corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]
    # Cronbach's Alpha lijst
    corevariable_ca_js = [round(cronbachs_alpha(corevariable, df), 4) for
                          corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]
    # Composite Reliability lijst
    corevariable_cr_js = [round(composite_reliability(corevariable, df, config, Scheme.CENTROID), 4) for
                          corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]

    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()

    length_corevariables = len(corevariable_names_js_all)

    # VIF-waarden
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()
    dct_of_all_vifs = outer_vif_values_dict(df, questionnaire)
    corevariable_vif_js = [dct_of_all_vifs[key] for key in dct_of_all_vifs if key[:length_abbreviation] ==
                           corevariable.abbreviation]

    # HTMT-waarden
    corevariables_htmt = corevariables
    corevariables_htmt.remove(corevariable)
    length_corevariables_htmt = len(corevariables_htmt)
    corevariable_names_htmt_js = corevariables_htmt[:3]
    corevariable_htmt_js = [round(heterotrait_monotrait(corevariable, lv, correlation_matrix(df), df), 4)
                            for lv in corevariables_htmt[:3]]
    corevariable_htmt_js_all = [round(heterotrait_monotrait(corevariable, lv, correlation_matrix(df), df), 4)
                                for lv in corevariables_htmt]

    # Ladingen van de items
    loadings_dct = pd.DataFrame(model1['loading']).to_dict('dict')['loading']
    loadings_list = [loadings_dct[item] for item in items_lv]

    return render_template('new_study/corevariable_analysis.html', study_code=study_code, corevariable=corevariable,
                           corevariables=corevariables, corevariable_names_js=corevariable_names_js,
                           corevariable_ave_js=corevariable_ave_js, corevariable_ca_js=corevariable_ca_js,
                           corevariable_cr_js=corevariable_cr_js, corevariable_names_js_all=corevariable_names_js_all,
                           corevariable_ave_js_all=corevariable_ave_js_all, items_lv=items_lv, length_items_lv=length_items_lv,
                           corevariable_ca_js_all=corevariable_ca_js_all, corevariable_vif_js=corevariable_vif_js,
                           corevariable_cr_js_all=corevariable_cr_js_all, length_corevariables=length_corevariables,
                           loadings_list=loadings_list, corevariables_htmt=corevariables_htmt,
                           corevariable_htmt_js=corevariable_htmt_js, corevariable_names_htmt_js=corevariable_names_htmt_js,
                           length_corevariables_htmt=length_corevariables_htmt, corevariable_htmt_js_all=corevariable_htmt_js_all)

