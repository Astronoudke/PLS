from flask import redirect, url_for
from flask_login import current_user

import math

from app.models import Study


def check_authorization(name_study):
    study = Study.query.filter_by(name=name_study).first()
    if current_user not in study.linked_users:
        print("Not authorized")
        return redirect(url_for('main.not_authorized'))


def check_stages(name_study):
    study = Study.query.filter_by(name=name_study).first()
    if study.stage_2:
        return redirect(url_for('new_study.study_underway', name_study=name_study, study_code=study.code))


# Berekeningen

def variance(items, dataset):
    if len(items) == 1:
        item = items[0]
        scores = [score for score in dataset[item]]
        average = sum(scores) / len(scores)
        differences_squared = [(score - average) * (score - average) for score in scores]

        return sum(differences_squared) / (len(scores))

    else:
        scores_per_case = {}
        scores = len([score for score in dataset[items[0]]])
        for question in items:
            for row in range(scores):
                if row in scores_per_case:
                    scores_per_case[row].append(dataset[question][row])
                else:
                    scores_per_case[row] = []
                    scores_per_case[row].append(dataset[question][row])

        list_of_totals = [sum(scores_per_case[case]) for case in scores_per_case]

        average = sum(list_of_totals) / len(list_of_totals)
        differences_squared = [(score - average) * (score - average) for score in list_of_totals]

        return sum(differences_squared) / (len(list_of_totals))


def cronbachs_alpha(sub_latent_variable, dataset):
    questions = [i for i in [question for question in dataset if question[:2] == sub_latent_variable.abbreviation]]
    total_items = len(questions)
    variance_total_column = variance(questions, dataset)
    variance_questions = [variance([question], dataset) for question in questions]

    return (total_items / (total_items - 1)) * ((variance_total_column - sum(variance_questions)) / variance_total_column)
