from flask import redirect, url_for
from flask_login import current_user
import plspm.config as c
from plspm.plspm import Plspm
from plspm.scheme import Scheme
from plspm.mode import Mode
import math
import pandas as pd

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


def cronbachs_alpha(latent_variable, dataset):
    questions = [i for i in [question for question in dataset if question[:2] == latent_variable.abbreviation]]
    total_items = len(questions)
    variance_total_column = variance(questions, dataset)
    variance_questions = [variance([question], dataset) for question in questions]

    return (total_items / (total_items - 1)) * ((variance_total_column - sum(variance_questions)) / variance_total_column)


def composite_reliability(latent_variable, dataset, configuration, scheme):
    plspm_calc = Plspm(dataset, configuration, scheme)
    model = plspm_calc.outer_model()

    # Creëer dictionary met alleen loadings van latente variabele
    loadings_dct = pd.DataFrame(model['loading']).to_dict('dict')['loading']
    not_questions = [question for question in loadings_dct if question[:2] != latent_variable.abbreviation]
    loadings_dct = {key: loadings_dct[key] for key in loadings_dct if key not in not_questions}

    loadings = [loadings_dct[i] for i in loadings_dct]
    loadings_squared = [score * score for score in loadings]
    errors = [1 - score for score in loadings_squared]

    return (sum(loadings) * sum(loadings)) / ((sum(loadings) * sum(loadings)) + sum(errors))


def average_variance_extracted(latent_variable, dataset, configuration, scheme):
    plspm_calc = Plspm(dataset, configuration, scheme)
    model = plspm_calc.outer_model()

    # Creëer dictionary met alleen loadings van latente variabele
    loadings_dct = pd.DataFrame(model['loading']).to_dict('dict')['loading']
    not_questions = [question for question in loadings_dct if question[:2] != latent_variable.abbreviation]
    loadings_dct = {key: loadings_dct[key] for key in loadings_dct if key not in not_questions}

    loadings = [loadings_dct[i] for i in loadings_dct]
    loadings_squared = [score * score for score in loadings]
    population = len(loadings)

    return sum(loadings_squared) / population
