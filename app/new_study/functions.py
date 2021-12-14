from flask import redirect, url_for
from flask_login import current_user
import plspm.config as c
from plspm.plspm import Plspm
from plspm.scheme import Scheme
from plspm.mode import Mode
import math
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from app.models import Study, Question, QuestionGroup


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
    length_abbreviation = len(latent_variable.abbreviation)
    questions = [i for i in
                 [question for question in dataset if question[:length_abbreviation] == latent_variable.abbreviation]]
    total_items = len(questions)
    variance_total_column = variance(questions, dataset)
    variance_questions = [variance([question], dataset) for question in questions]

    return (total_items / (total_items - 1)) * (
            (variance_total_column - sum(variance_questions)) / variance_total_column)


def composite_reliability(latent_variable, dataset, configuration, scheme):
    length_abbreviation = len(latent_variable.abbreviation)
    plspm_calc = Plspm(dataset, configuration, scheme)
    model = plspm_calc.outer_model()

    # Creëer dictionary met alleen loadings van latente variabele
    loadings_dct = pd.DataFrame(model['loading']).to_dict('dict')['loading']
    # :2 MOET AANGEPAST WORDEN OP AFKORTINGEN LANGER DAN DRIE LETTERS
    not_questions = [question for question in loadings_dct if
                     question[:length_abbreviation] != latent_variable.abbreviation]
    loadings_dct = {key: loadings_dct[key] for key in loadings_dct if key not in not_questions}

    loadings = [loadings_dct[i] for i in loadings_dct]
    loadings_squared = [score * score for score in loadings]
    errors = [1 - score for score in loadings_squared]

    return (sum(loadings) * sum(loadings)) / ((sum(loadings) * sum(loadings)) + sum(errors))


def average_variance_extracted(latent_variable, dataset, configuration, scheme):
    length_abbreviation = len(latent_variable.abbreviation)
    plspm_calc = Plspm(dataset, configuration, scheme)
    model = plspm_calc.outer_model()

    # Creëer dictionary met alleen loadings van latente variabele
    loadings_dct = pd.DataFrame(model['loading']).to_dict('dict')['loading']
    not_questions = [question for question in loadings_dct if
                     question[:length_abbreviation] != latent_variable.abbreviation]
    loadings_dct = {key: loadings_dct[key] for key in loadings_dct if key not in not_questions}

    loadings = [loadings_dct[i] for i in loadings_dct]
    loadings_squared = [score * score for score in loadings]
    population = len(loadings)

    return sum(loadings_squared) / population


def covariance(item1, item2, dataset):
    scores_item1 = []
    scores_item2 = []
    # Voor het geval de correlatie-matrix wordt uitgerekend
    if item1 == item2:
        for item in dataset:
            if item == item1:
                for score in dataset[item]:
                    scores_item1.append(score)
                    scores_item2.append(score)
    else:
        for item in dataset:
            if item == item1:
                for score in dataset[item]:
                    scores_item1.append(score)
            elif item == item2:
                for score in dataset[item]:
                    scores_item2.append(score)

    avg_item1 = sum(scores_item1) / len(scores_item1)
    avg_item2 = sum(scores_item2) / len(scores_item2)

    combination_of_scores = zip(scores_item1, scores_item2)
    combination_of_differences = [(x - avg_item1, y - avg_item2) for (x, y) in tuple(combination_of_scores)]
    differences_combined = [x * y for (x, y) in combination_of_differences]

    return sum(differences_combined) / len(differences_combined)


def pearson_correlation(lv1, lv2, dataset):
    covar = covariance(lv1, lv2, dataset)
    sd_lv1 = math.sqrt(variance([lv1], dataset))
    sd_lv2 = math.sqrt(variance([lv2], dataset))

    return covar / (sd_lv1 * sd_lv2)


def correlation_matrix(dataset):
    data = {}
    items = [i for i in [item for item in dataset]]
    for item in items:
        data[item] = []
        not_valuable = False
        for lv2 in items:
            if round(pearson_correlation(item, lv2, dataset), 4) == 1:
                not_valuable = True
            if not_valuable:
                data[item].append(np.nan)
            else:
                data[item].append(pearson_correlation(item, lv2, dataset))

    # data = {}
    # items = [i for i in [item for item in dataset]]
    # for item in items:
    #   data[item] = [pearson_correlation(item, lv2, dataset) for lv2 in items]
    df = pd.DataFrame(data, index=[item for item in items])
    df = df.transpose()

    return df


def heterotrait_monotrait(var1, var2, corr_matrix, dataset):
    length_abbreviation_var1 = len(var1.abbreviation)
    items_var1 = [i for i in [item for item in dataset if item[:length_abbreviation_var1] == var1.abbreviation]]
    length_abbreviation_var2 = len(var2.abbreviation)
    items_var2 = [i for i in [item for item in dataset if item[:length_abbreviation_var2] == var2.abbreviation]]

    monotrait_var1_list = []
    monotrait_var2_list = []
    heterotrait_list = []

    for item_1 in items_var1:
        for item_2 in corr_matrix[item_1].keys():
            if item_2 in items_var1 and not math.isnan(corr_matrix[item_1][item_2]):
                monotrait_var1_list.append(corr_matrix[item_1][item_2])

    for item_1 in items_var2:
        for item_2 in corr_matrix[item_1].keys():
            if item_2 in items_var2 and not math.isnan(corr_matrix[item_1][item_2]):
                monotrait_var2_list.append(corr_matrix[item_1][item_2])

    for item_1 in items_var1:
        for item_2 in corr_matrix[item_1].keys():
            if item_2 in items_var2 and not math.isnan(corr_matrix[item_1][item_2]):
                heterotrait_list.append(corr_matrix[item_1][item_2])

            if item_2 in items_var2 and math.isnan(corr_matrix[item_1][item_2]):
                if not math.isnan(corr_matrix[item_2][item_1]):
                    heterotrait_list.append(corr_matrix[item_2][item_1])

    avg_heterotrait = sum(heterotrait_list) / len(heterotrait_list)
    avg_monotrait_var1 = sum(monotrait_var1_list) / len(monotrait_var1_list)
    avg_monotrait_var2 = sum(monotrait_var2_list) / len(monotrait_var2_list)

    return avg_heterotrait / (math.sqrt(avg_monotrait_var1 * avg_monotrait_var2))


def htmt_matrix(dataset, model):
    corevariables = [corevariable for corevariable in model.linked_corevariables]
    data = {}
    for corevariable in corevariables:
        data[corevariable.abbreviation] = []
        not_valuable = False
        for cv2 in corevariables:
            if round(heterotrait_monotrait(corevariable, cv2, correlation_matrix(dataset), dataset), 4) == 1:
                not_valuable = True
            if not_valuable:
                data[corevariable.abbreviation].append(' ')
            else:
                data[corevariable.abbreviation].append(round(
                    heterotrait_monotrait(corevariable, cv2, correlation_matrix(dataset), dataset),4))

    df = pd.DataFrame(data, index=[corevariable.abbreviation for corevariable in corevariables])
    df = df.transpose()

    return df


def outer_vif_values_dict(dataset, questionnaire):
    abbreviations_by_lv = []
    questiongroups = [questiongroup for questiongroup in
                      QuestionGroup.query.filter_by(questionnaire_id=questionnaire.id)]
    for questiongroup in questiongroups:
        questions = [question for question in Question.query.filter_by(questiongroup_id=questiongroup.id)]
        abbreviations_by_lv.append([question.question_code for question in questions])

    dataframes_vif = []
    for questiongroup in abbreviations_by_lv:
        X = add_constant(dataset[questiongroup])
        # VIF dataframe
        vif_data = pd.DataFrame()
        vif_data["feature"] = X.columns

        # calculating VIF for each feature
        vif_data["VIF"] = [variance_inflation_factor(X.values, i)
                           for i in range(len(X.columns))]

        dataframes_vif.append(vif_data)

    result = pd.concat(dataframes_vif)
    result_outer_vif = result[result.feature != 'const']

    data_outer_vif = {}
    for i in range(len(result_outer_vif)):
        data_outer_vif[result_outer_vif.iloc[i]['feature']] = round(float(result_outer_vif.iloc[i]['VIF']), 4)

    return data_outer_vif
