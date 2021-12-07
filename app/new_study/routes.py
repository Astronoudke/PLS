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
    covariance, \
    pearson_correlation, correlation_matrix, heterotrait_monotrait, htmt_matrix
from statsmodels.stats.outliers_influence import variance_inflation_factor


#############################################################################################################
#                                        Setting up the study
#############################################################################################################


@bp.route('/new_study', methods=['GET', 'POST'])
@login_required
def new_study():
    form = CreateNewStudyForm()
    if form.validate_on_submit():
        # Create new model
        new_model = UTAUTmodel(name="UTAUT")
        db.session.add(new_model)
        db.session.commit()

        for abbreviation in ["PE", "EE", "SI", "FC", "BI", "UB"]:
            corevariable = CoreVariable.query.filter_by(abbreviation=abbreviation).first()
            corevariable.link(new_model)

        for sublist in [["PE", "BI"], ["EE", "BI"], ["SI", "BI"], ["FC", "UB"], ["BI", "UB"]]:
            id_influencer = CoreVariable.query.filter_by(
                abbreviation=sublist[0]).first().id
            id_influenced = CoreVariable.query.filter_by(
                abbreviation=sublist[1]).first().id

            newrelation = Relation(model_id=new_model.id,
                                   influencer_id=id_influencer,
                                   influenced_id=id_influenced)
            db.session.add(newrelation)
            db.session.commit()

        # Create new study
        new_study = Study(name=form.name_of_study.data, description=form.description_of_study.data,
                          technology=form.technology_of_study.data, model_id=new_model.id)
        new_study.create_code()
        db.session.add(new_study)
        db.session.commit()

        current_user.link(new_study)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=new_study.code))
    return render_template("new_study/new_study.html", title='New Study', form=form)


@bp.route('/edit_study/<study_code>', methods=['GET', 'POST'])
@login_required
def edit_study(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    form = EditStudyForm(study.name, study.description, study.technology)
    if form.validate_on_submit():
        study.name = form.name_of_study.data
        study.description = form.description_of_study.data
        study.technology = form.technology_of_study.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('new_study.utaut', study_code=study.code))
    elif request.method == 'GET':
        form.name_of_study.data = study.name
        form.description_of_study.data = study.description
        form.technology_of_study.data = study.technology
    return render_template('new_study/edit_study.html', title='Edit Profile',
                           form=form, study=study)


@bp.route('/add_user/<study_code>', methods=['GET', 'POST'])
@login_required
def add_user(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

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
#                                               UTAUT
#############################################################################################################

@bp.route('/utaut/<study_code>', methods=['GET', 'POST'])
@login_required
def utaut(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    core_variables = [corevariable for corevariable in model.linked_corevariables]
    relations = [relation for relation in Relation.query.filter_by(model_id=model.id)]
    existing_models = [models for models in UTAUTmodel.query.all()]

    form_add_variable = AddCoreVariable()
    form_add_variable.add_variable.choices = [(core_variable.id, core_variable.name) for core_variable in
                                              CoreVariable.query.filter_by(user_id=current_user.id)] + \
                                             [(core_variable.id, core_variable.name) for core_variable in
                                              CoreVariable.query.filter_by(user_id=None)]

    form = ChooseNewModel()
    form.new_model.choices = [(utautmodel.id, utautmodel.name) for utautmodel in
                              UTAUTmodel.query.all()]

    if form_add_variable.validate_on_submit():
        core_variable = CoreVariable.query.filter_by(id=form_add_variable.add_variable.data).first()
        core_variable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=study_code))

    return render_template("new_study/utaut.html", title='UTAUT', study=study, model=model,
                           core_variables=core_variables,
                           relations=relations, existing_models=existing_models, form=form,
                           form_add_variable=form_add_variable)


@bp.route('/utaut/new_core_variable/<study_code>', methods=['GET', 'POST'])
@login_required
def new_core_variable(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(code=study_code).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    form = CreateNewCoreVariableForm()

    if form.validate_on_submit():
        study = Study.query.filter_by(code=study_code).first()
        new_corevariable = CoreVariable(name=form.name_corevariable.data,
                                        abbreviation=form.abbreviation_corevariable.data,
                                        description=form.description_corevariable.data,
                                        user_id=current_user.id)
        db.session.add(new_corevariable)
        db.session.commit()

        model = UTAUTmodel.query.filter_by(id=study.model_id).first()

        new_corevariable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', study_code=study_code))

    return render_template("new_study/new_corevariable.html", title='New Core Variable', form=form)


@bp.route('/remove_core_variable/<study_code>/<corevariable_id>', methods=['GET', 'POST'])
@login_required
def remove_core_variable(study_code, corevariable_id):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()

    corevariable.unlink(model)
    db.session.commit()
    Relation.query.filter_by(influencer_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()
    Relation.query.filter_by(influenced_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()

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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    form = CreateNewRelationForm()

    if form.validate_on_submit():
        model = UTAUTmodel.query.filter_by(id=study.model_id).first()

        id_influencer = CoreVariable.query.filter_by(
            abbreviation=form.abbreviation_influencer.data).first().id
        id_influenced = CoreVariable.query.filter_by(
            abbreviation=form.abbreviation_influenced.data).first().id

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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    Relation.query.filter_by(id=id_relation).delete()
    db.session.commit()

    return redirect(url_for('new_study.utaut', study_code=study_code))


#############################################################################################################
#                                           Questionnaire
#############################################################################################################


@bp.route('/pre_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def pre_questionnaire(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    # create questionnaire if no questionnaire exists yet
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    if Questionnaire.query.filter_by(study_id=study.id).first() is None:
        newquestionnaire = Questionnaire(study_id=study.id)
        db.session.add(newquestionnaire)
        db.session.commit()

        for corevariable in model.linked_corevariables:
            questiongroup = QuestionGroup(title=corevariable.name, group_type="likert",
                                          questionnaire_id=newquestionnaire.id,
                                          corevariable_id=corevariable.id)
            db.session.add(questiongroup)
            db.session.commit()

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    form = ScaleForm(questionnaire.scale)

    if form.validate_on_submit():
        questionnaire.scale = form.scale.data
        db.session.commit()
        return redirect(url_for('new_study.questionnaire', study_code=study_code))

    return render_template("new_study/pre_questionnaire.html", title='Pre-questionnaire', study=study, model=model,
                           form=form)


@bp.route('/questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def questionnaire(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    for core_variable in model.linked_corevariables:
        if core_variable.id not in [questiongroup.corevariable_id for questiongroup
                                    in QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]:
            questiongroup = QuestionGroup(title=core_variable.name, group_type="likert",
                                          questionnaire_id=questionnaire.id,
                                          corevariable_id=core_variable.id)
            db.session.add(questiongroup)
            db.session.commit()

    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]
    questions = []
    for questiongroup in questiongroups:
        questions.append(
            [question for question in
             Question.query.filter_by(questiongroup_id=questiongroup.id).all()])
    questiongroups_questions = dict(zip(questiongroups, questions))

    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]

    return render_template("new_study/questionnaire.html", title='Questionnaire', study=study, model=model,
                           questiongroups=questiongroups, questionnaire=questionnaire,
                           questiongroups_questions=questiongroups_questions, demographics=demographics)


@bp.route('/questionnaire/switch_reversed_score/<study_code>/<name_question>', methods=['GET', 'POST'])
@login_required
def switch_reversed_score(study_code, name_question):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    study = Study.query.filter_by(code=study_code).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    standard_questions = [standard_question for standard_question in StandardQuestion.query.filter_by(user_id=user.id)]
    for standard_question in standard_questions:
        replaced_name_question = standard_question.question.replace('(...)', study.technology)
        replaced_name_question = replaced_name_question.replace('(…)', study.technology)
        corresponding_questiongroup = QuestionGroup.query.filter_by(
            corevariable_id=standard_question.corevariable_id, questionnaire_id=questionnaire.id).first()

        corevariable = CoreVariable.query.filter_by(name=corresponding_questiongroup.title,
                                                    user_id=current_user.id).first()
        if corevariable is None:
            corevariable = CoreVariable.query.filter_by(name=corresponding_questiongroup.title, user_id=None).first()

        if corevariable is not None:
            abbreviation_corevariable = corevariable.abbreviation
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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    study = Study.query.filter_by(code=study_code).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic.name for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]

    standard_demographics = [standard_demographic for standard_demographic in
                             StandardDemographic.query.filter_by(user_id=user.id)]
    for standard_demographic in standard_demographics:
        new_demographic = Demographic(name=standard_demographic.name,
                                      description=standard_demographic.description,
                                      choices=standard_demographic.choices,
                                      optional=standard_demographic.optional,
                                      questiontype_name=standard_demographic.questiontype_name,
                                      questionnaire_id=questionnaire.id)
        if new_demographic.name not in demographics:
            db.session.add(new_demographic)
            db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/new_question/<name_questiongroup>/<study_code>', methods=['GET', 'POST'])
@login_required
def new_question(name_questiongroup, study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    form = CreateNewQuestion()

    if form.validate_on_submit():
        questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
        questiongroup = QuestionGroup.query.filter_by(title=name_questiongroup,
                                                      questionnaire_id=questionnaire.id).first()

        corevariable = CoreVariable.query.filter_by(name=questiongroup.title, user_id=current_user.id).first()
        if corevariable is None:
            corevariable = CoreVariable.query.filter_by(name=questiongroup.title, user_id=None).first()

        abbreviation_corevariable = corevariable.abbreviation
        new_code = abbreviation_corevariable + str(len([question for question in
                                                        Question.query.filter_by(
                                                            questiongroup_id=questiongroup.id)]) + 1)
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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    Question.query.filter_by(question=name_question).delete()
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study_code))


@bp.route('/questionnaire/new_demographic/<study_code>', methods=['GET', 'POST'])
@login_required
def new_demographic(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    form = CreateNewDemographicForm()

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
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    Demographic.query.filter_by(id=id_demographic).delete()
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', study_code=study.code))


@bp.route('/check_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def check_questionnaire(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study.code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    questiongroups = [questiongroup for questiongroup in questionnaire.linked_questiongroups]

    for questiongroup in questiongroups:
        if Question.query.filter_by(questiongroup_id=questiongroup.id).count() == 0:
            flash('One or more of the core variables does not have questions yet. Please add at least one question to '
                  'each core variable.')
            return redirect(url_for('new_study.questionnaire', study_code=study.code))

    return redirect(url_for('new_study.start_study', study_code=study.code))


#############################################################################################################
#                                            Start Study
#############################################################################################################

@bp.route('/start_study/<study_code>', methods=['GET', 'POST'])
@login_required
def start_study(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    study.stage_1 = False
    study.stage_2 = True
    db.session.commit()

    return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))


@bp.route('/study_underway/<name_study>/<study_code>', methods=['GET', 'POST'])
@login_required
def study_underway(name_study, study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    study = Study.query.filter_by(name=name_study).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))
    link = '127.0.0.1:5000/d/e/{}'.format(study.code)

    return render_template('new_study/study_underway.html', title="Underway: {}".format(name_study), study=study,
                           link=link, questionnaire=questionnaire)


@bp.route('/end_questionnaire/<study_code>', methods=['GET', 'POST'])
@login_required
def end_questionnaire(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))

    if study.stage_3:
        return redirect(url_for('new_study.summary_results', study_code=study_code))

    study.stage_2 = False
    study.stage_3 = True
    db.session.commit()

    return redirect(url_for('new_study.summary_results', study_code=study_code))


#############################################################################################################
#                                           Data Analysis
#############################################################################################################


@bp.route('/summary_results/<study_code>', methods=['GET', 'POST'])
@login_required
def summary_results(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographics = [demographic for demographic in Demographic.query.filter_by(questionnaire_id=questionnaire.id)]
    total_cases = [case for case in Case.query.filter_by(questionnaire_id=questionnaire.id)]

    # Summary van de demografische resultaten
    cases = []
    for case in total_cases:
        for i in range(len(demographics)):
            cases.append(case.id)
    demos = []
    for case in total_cases:
        for demographic in demographics:
            demos.append(demographic.name)

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

    print(dct_demographics)
    # Summary van de vragenlijstresultaten voor iedere case
    questiongroups = [questiongroup for questiongroup in
                      QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]
    questions = []
    for questiongroup in questiongroups:
        list_of_questions = [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]
        for question in list_of_questions:
            questions.append(question)
    cases = []
    for case in total_cases:
        for i in range(len(questions)):
            cases.append(case.id)
    quests = []
    for case in total_cases:
        for question in questions:
            quests.append(question.question)

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

    # Summary van de gemiddeldes en standaarddeviaties voor iedere vraag
    questiongroups = [questiongroup for questiongroup in
                      QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]

    dct_questions = {}
    for questiongroup in questiongroups:
        for question in [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]:
            dct_questions[question] = []

    for question in dct_questions:
        answer_scores = []
        for answer in [answer for answer in Answer.query.filter_by(question_id=question.id)]:
            answer_scores.append(int(answer.score))
        array = np.array(answer_scores)
        dct_questions[question].extend([round(np.average(array), 2), round(np.std(array), 2)])

    return render_template('new_study/summary_results.html', study_code=study_code, demographics=demographics,
                           cases=cases, dct_demographics=dct_demographics, dct_answers=dct_answers, questions=questions,
                           dct_questions=dct_questions)


@bp.route('/data_analysis/<study_code>', methods=['GET', 'POST'])
@login_required
def data_analysis(study_code):
    # check authorization
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    corevariables = [corevariable for corevariable in model.linked_corevariables]

    # Set up dataframe
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
    print(df)

    X = df[[i for i in df]]
    vif_data = pd.DataFrame()
    vif_data["feature"] = X.columns

    # calculating VIF for each feature
    vif_data["VIF"] = [variance_inflation_factor(X.values, i)
                       for i in range(len(X.columns))]

    print(vif_data)
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

    data_construct_validity = {}
    for corevariable in corevariables:
        data_construct_validity[corevariable] = [round(cronbachs_alpha(corevariable, df), 4),
                                                 round(composite_reliability(corevariable, df, config, Scheme.CENTROID),
                                                       4),
                                                 round(average_variance_extracted(corevariable, df, config,
                                                                                  Scheme.CENTROID), 4)]

    data_htmt = htmt_matrix(df, model)
    amount_of_variables = len(corevariables)

    return render_template('new_study/data_analysis.html', study_code=study_code,
                           data_construct_validity=data_construct_validity,
                           data_htmt=data_htmt, amount_of_variables=amount_of_variables, study=study)


@bp.route('/data_analysis/corevariable_analysis/<study_code>/<corevariable_id>', methods=['GET', 'POST'])
@login_required
def corevariable_analysis(study_code, corevariable_id):
    study = Study.query.filter_by(code=study_code).first()
    if current_user not in study.linked_users:
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    if study.stage_1:
        return redirect(url_for('new_study.utaut', study_code=study_code))
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=study.name, study_code=study_code))

    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()
    corevariables = [corevariable for corevariable in model.linked_corevariables]

    # Set up dataframe
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

    construct_data = [[round(cronbachs_alpha(corevariable, df), 4),
                       round(composite_reliability(corevariable, df, config, Scheme.CENTROID), 4),
                       round(average_variance_extracted(corevariable, df, config, Scheme.CENTROID), 4)] for corevariable
                       in corevariables]

    # Voor alle kernvariabelen
    corevariable_names_js_all = [corevariable for corevariable in model.linked_corevariables]
    corevariable_ave_js_all = [round(average_variance_extracted(corevariable, df, config, Scheme.CENTROID), 4) for
                               corevariable in corevariables]
    corevariable_ca_js_all = [round(cronbachs_alpha(corevariable, df), 4) for corevariable in corevariables]
    corevariable_cr_js_all = [round(composite_reliability(corevariable, df, config, Scheme.CENTROID), 4) for corevariable
                              in corevariables]

    length_corevariables = len(corevariable_names_js_all)

    # Voor drie kernvariabelen
    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()
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

    corevariable_names_js = [corevariable for corevariable in
                             [corevariables[indexes_corevariables[0]], corevariables[indexes_corevariables[1]],
                              corevariables[indexes_corevariables[2]]]]
    corevariable_ave_js = [round(average_variance_extracted(corevariable, df, config, Scheme.CENTROID), 4) for
                           corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]
    corevariable_ca_js = [round(cronbachs_alpha(corevariable, df), 4) for
                          corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]
    corevariable_cr_js = [round(composite_reliability(corevariable, df, config, Scheme.CENTROID), 4) for
                          corevariable in corevariables[indexes_corevariables[0]:indexes_corevariables[2] + 1]]

    corevariable = CoreVariable.query.filter_by(id=corevariable_id).first()

    return render_template('new_study/corevariable_analysis.html', study_code=study_code, corevariable=corevariable,
                           corevariables=corevariables, corevariable_names_js=corevariable_names_js,
                           corevariable_ave_js=corevariable_ave_js, corevariable_ca_js=corevariable_ca_js,
                           corevariable_cr_js=corevariable_cr_js, corevariable_names_js_all=corevariable_names_js_all,
                           corevariable_ave_js_all=corevariable_ave_js_all, corevariable_ca_js_all=corevariable_ca_js_all,
                           corevariable_cr_js_all=corevariable_cr_js_all, length_corevariables=length_corevariables)
