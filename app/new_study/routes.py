from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.new_study.forms import CreateNewStudyForm, CreateNewCoreVariableForm, CreateNewRelationForm, \
    CreateNewQuestion, ChooseNewModel, AddCoreVariable, EditStudyForm, AddDemographic, AddUserForm, ScaleForm
from app.models import User, Study, UTAUTmodel, CoreVariable, Relation, Questionnaire, Question, StandardQuestion, \
    QuestionGroup, Case, Demographic
from app.new_study import bp
from app.new_study.functions import check_authorization, check_stages
from wtforms import StringField


@bp.route('/new_study', methods=['GET', 'POST'])
@login_required
def new_study():
    form = CreateNewStudyForm()
    if form.validate_on_submit():
        #Create new model
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

        #Create new study
        new_study = Study(name=form.name_of_study.data, description=form.description_of_study.data,
                          technology=form.technology_of_study.data, model_id=new_model.id)
        db.session.add(new_study)
        db.session.commit()

        current_user.link(new_study)
        db.session.commit()

        return redirect(url_for('new_study.utaut', name_study=new_study.name))
    return render_template("new_study/new_study.html", title='New Study', form=form)


@bp.route('/edit_study/<name_study>', methods=['GET', 'POST'])
@login_required
def edit_study(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    form = EditStudyForm(name_study, study.description, study.technology)
    if form.validate_on_submit():
        study.name = form.name_of_study.data
        study.description = form.description_of_study.data
        study.technology = form.technology_of_study.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('new_study.utaut', name_study=form.name_of_study.data))
    elif request.method == 'GET':
        form.name_of_study.data = name_study
        form.description_of_study.data = study.description
        form.technology_of_study.data = study.technology
    return render_template('new_study/edit_study.html', title='Edit Profile',
                           form=form)


@bp.route('/add_user/<name_study>', methods=['GET', 'POST'])
@login_required
def add_user(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    form = AddUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name_user.data).first()
        user.link(study)
        db.session.commit()

        flash('Your changes have been saved.')
        return redirect(url_for('new_study.edit_study', name_study=name_study))

    return render_template('new_study/add_user.html', title='Edit Profile',
                           form=form)


#############################################################################################################
#                                              UTAUT
#############################################################################################################


@bp.route('/utaut/<name_study>', methods=['GET', 'POST'])
@login_required
def utaut(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    core_variables = [corevariable for corevariable in model.linked_corevariables]
    relations = [relation for relation in Relation.query.filter_by(model_id=model.id)]
    existing_models = [models for models in UTAUTmodel.query.all()]

    form_add_variable = AddCoreVariable()
    form_add_variable.add_variable.choices = [(core_variable.id, core_variable.name) for core_variable in
                                              CoreVariable.query.all()]

    form = ChooseNewModel()
    form.new_model.choices = [(utautmodel.id, utautmodel.name) for utautmodel in
                              UTAUTmodel.query.all()]

    if form_add_variable.validate_on_submit():
        core_variable = CoreVariable.query.filter_by(id=form_add_variable.add_variable.data).first()
        core_variable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', name_study=name_study))

    return render_template("new_study/utaut.html", title='UTAUT', study=study, model=model,
                           core_variables=core_variables,
                           relations=relations, existing_models=existing_models, form=form,
                           form_add_variable=form_add_variable)


@bp.route('/utaut/new_core_variable/<name_study>', methods=['GET', 'POST'])
@login_required
def new_core_variable(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    form = CreateNewCoreVariableForm()

    if form.validate_on_submit():
        study = Study.query.filter_by(name=name_study).first()
        new_corevariable = CoreVariable(name=form.name_corevariable.data,
                                        abbreviation=form.abbreviation_corevariable.data,
                                        description=form.description_corevariable.data)
        db.session.add(new_corevariable)
        db.session.commit()

        model = UTAUTmodel.query.filter_by(id=study.model_id).first()

        new_corevariable.link(model)
        db.session.commit()

        return redirect(url_for('new_study.utaut', name_study=name_study))

    return render_template("new_study/new_corevariable.html", title='New Core Variable', form=form)


@bp.route('/remove_core_variable/<name_study>/<name_core_variable>', methods=['GET', 'POST'])
@login_required
def remove_core_variable(name_study, name_core_variable):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    corevariable = CoreVariable.query.filter_by(name=name_core_variable).first()

    corevariable.unlink(model)
    db.session.commit()
    Relation.query.filter_by(influencer_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()
    Relation.query.filter_by(influenced_id=corevariable.id, model_id=model.id).delete()
    db.session.commit()

    if questionnaire:
        questiongroup = QuestionGroup.query.filter_by(title=name_core_variable,
                                                      questionnaire_id=questionnaire.id).first()
        Question.query.filter_by(questiongroup_id=questiongroup.id).delete()
        db.session.commit()
        QuestionGroup.query.filter_by(title=name_core_variable, questionnaire_id=questionnaire.id).delete()
        db.session.commit()

    return redirect(url_for('new_study.utaut', name_study=name_study))


@bp.route('/utaut/new_relation/<name_study>', methods=['GET', 'POST'])
@login_required
def new_relation(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    form = CreateNewRelationForm()

    if form.validate_on_submit():
        study = Study.query.filter_by(name=name_study).first()
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

        return redirect(url_for('new_study.utaut', name_study=name_study))

    return render_template("new_study/new_relation.html", title='New Relation', form=form)


@bp.route('/remove_relation/<name_study>/<id_relation>', methods=['GET', 'POST'])
@login_required
def remove_relation(name_study, id_relation):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    Relation.query.filter_by(id=id_relation).delete()
    db.session.commit()

    return redirect(url_for('new_study.utaut', name_study=name_study))


#############################################################################################################
#                                              Questionnaire
#############################################################################################################


@bp.route('/create_questionnaire/<name_study>', methods=['GET', 'POST'])
@login_required
def create_questionnaire(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
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

    return redirect(url_for('new_study.pre_questionnaire', name_study=name_study))


@bp.route('/pre_questionnaire/<name_study>', methods=['GET', 'POST'])
@login_required
def pre_questionnaire(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    form = ScaleForm()

    if form.validate_on_submit():
        questionnaire.scale = form.scale.data
        db.session.commit()
        return redirect(url_for('new_study.questionnaire', name_study=name_study))

    return render_template("new_study/pre_questionnaire.html", title='Pre-questionnaire', study=study, model=model, form=form)


@bp.route('/questionnaire/<name_study>', methods=['GET', 'POST'])
@login_required
def questionnaire(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    model = UTAUTmodel.query.filter_by(id=study.model_id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    form_add_demographic = AddDemographic()
    form_add_demographic.add_demographic.choices = [(demographic.id, demographic.name) for demographic in
                                                    Demographic.query.all()]

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

    if form_add_demographic.validate_on_submit():
        demographic = Demographic.query.filter_by(id=form_add_demographic.add_demographic.data).first()
        demographic.link(questionnaire)
        db.session.commit()

        return redirect(url_for('new_study.questionnaire', name_study=name_study))

    demographics = [demographic for demographic in questionnaire.linked_demographics]

    return render_template("new_study/questionnaire.html", title='Questionnaire', study=study, model=model,
                           questiongroups=questiongroups, questionnaire=questionnaire,
                           questiongroups_questions=questiongroups_questions, form_add_demographic=form_add_demographic,
                           demographics=demographics)


@bp.route('/questionnaire/switch_reversed_score/<name_study>/<name_question>', methods=['GET', 'POST'])
@login_required
def switch_reversed_score(name_study, name_question):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    question = Question.query.filter_by(question=name_question).first()
    if question.reversed_score:
        question.reversed_score = False
        db.session.commit()
    else:
        question.reversed_score = True
        db.session.commit()
    return redirect(url_for('new_study.questionnaire', name_study=name_study))


@bp.route('/questionnaire/use_standard_questions_questionnaire/<name_study>', methods=['GET', 'POST'])
@login_required
def use_standard_questions_questionnaire(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    user = User.query.filter_by(id=current_user.id).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()

    standard_questions = [standard_question for standard_question in StandardQuestion.query.filter_by(user_id=user.id)]
    for standard_question in standard_questions:
        replaced_name_question = standard_question.question.replace('(...)', study.technology)
        replaced_name_question = replaced_name_question.replace('(…)', study.technology)
        corresponding_questiongroup = QuestionGroup.query.filter_by(
            corevariable_id=standard_question.corevariable_id, questionnaire_id=questionnaire.id).first()
        newquestion = Question(question=replaced_name_question,
                               questiongroup_id=corresponding_questiongroup.id)
        db.session.add(newquestion)
        db.session.commit()

    return redirect(url_for('new_study.questionnaire', name_study=name_study))


@bp.route('/questionnaire/new_question/<name_questiongroup>/<name_study>', methods=['GET', 'POST'])
@login_required
def new_question(name_questiongroup, name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    form = CreateNewQuestion()

    if form.validate_on_submit():
        study = Study.query.filter_by(name=name_study).first()
        questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
        questiongroup = QuestionGroup.query.filter_by(title=name_questiongroup,
                                                      questionnaire_id=questionnaire.id).first()

        new_question = Question(question=form.name_question.data,
                                questiongroup_id=questiongroup.id)
        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for("new_study.questionnaire", name_study=name_study))

    return render_template("new_study/new_question.html", title="New Question", form=form)


@bp.route('/remove_question/<name_study>/<name_question>', methods=['GET', 'POST'])
@login_required
def remove_question(name_study, name_question):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    Question.query.filter_by(question=name_question).delete()
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', name_study=name_study))


@bp.route('/remove_demographic/<name_study>/<name_demographic>', methods=['GET', 'POST'])
@login_required
def remove_demographic(name_study, name_demographic):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    demographic = Demographic.query.filter_by(name=name_demographic).first()

    demographic.unlink(questionnaire)
    db.session.commit()

    return redirect(url_for('new_study.questionnaire', name_study=name_study))


#############################################################################################################
#                                              Start Study
#############################################################################################################


@bp.route('/start_study/<name_study>/', methods=['GET', 'POST'])
@login_required
def start_study(name_study):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    # check access to stage
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))

    study = Study.query.filter_by(name=name_study).first()
    study.create_code()
    db.session.commit()
    study.stage_1 = False
    study.stage_2 = True
    db.session.commit()

    study_code = study.code

    return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study_code))


@bp.route('/study_underway/<name_study>/<study_code>', methods=['GET', 'POST'])
@login_required
def study_underway(name_study, study_code):
    # check authorization
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))

    study = Study.query.filter_by(name=name_study).first()
    questionnaire = Questionnaire.query.filter_by(study_id=study.id).first()
    if study.stage_1:
        return redirect(url_for('new_study.utaut', name_study=name_study))
    link = '127.0.0.1:5000/e/e/{}'.format(study.code)

    return render_template('new_study/study_underway.html', title="Underway: {}".format(name_study), study=study,
                           link=link, questionnaire=questionnaire)
