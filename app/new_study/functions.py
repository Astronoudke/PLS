from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app.models import User, Study, UTAUTmodel, CoreVariable, Relation, Questionnaire, Question, StandardQuestion


def check_authorization(name_study):
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))


def check_stages(name_study):
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))
