'''
main simulation engine
test - k-fold cross validation using FMLA sample to check the following outcomes (predicted vs actual)

total number of leave takers
total number of leaves taken
total number of leave needers
mean prop_pay
individual accuracy of 'taker'
individual accuary of 'needer'
individual accuracy of 'prop_pay'

chris zhang 3/12/2019
'''
import pandas as pd
import numpy as np
import json
from time import time
from _5a_aux_functions import *
import sklearn.linear_model, sklearn.naive_bayes, sklearn.neighbors, sklearn.tree, sklearn.ensemble, \
    sklearn.gaussian_process, sklearn.svm
import math
from datetime import datetime
import matplotlib.pyplot as plt
import random
import json
from datetime import datetime

# Read in FMLA data
d = pd.read_csv('./data/fmla_2012/fmla_clean_2012.csv')
fold = 4 # validation parameter
part_size = int(round(len(d) / fold, 0))
types = ['own', 'matdis', 'bond', 'illchild', 'illspouse', 'illparent']

# def get_columns():
#     Xs = ['age', 'agesq', 'male', 'noHSdegree',
#           'BAplus', 'empgov_fed', 'empgov_st', 'empgov_loc',
#           'lnfaminc', 'black', 'asian', 'hisp', 'other',
#           'ndep_kid', 'ndep_old', 'nevermarried', 'partner',
#           'widowed', 'divorced', 'separated']
#     ys = ['take_own', 'take_matdis', 'take_bond', 'take_illchild', 'take_illspouse', 'take_illparent']
#     ys += ['need_own', 'need_matdis', 'need_bond', 'need_illchild', 'need_illspouse', 'need_illparent']
#     ys += ['resp_len']
#     w = 'weight'
#
#     return (Xs, ys, w)
#
# def get_sim_col(X, y, w, Xa, clf):
#     '''
#
#     :param X: training data predictors
#     :param y: training data outcomes
#     :param w: training data weights
#     :param Xa: test / target data predictors
#     :param clf: classifier instance
#     :return:
#     '''
#     # Data preparing - fill in nan
#     X = fillna_df(X)
#     y = fillna_df(pd.DataFrame(y))
#     y = y[y.columns[0]]
#     Xa = fillna_df(Xa)
#
#     # if clf = 'random draw'
#     if clf=='random draw':
#         yhat = [y.iloc[z] for z in np.random.choice(len(y), len(Xa))]
#         simcol = pd.Series(yhat)
#         simcol.name = y.name
#         return simcol
#     # if clf = some ML method
#     else:
#         # Data preparing - categorization for Naive Bayes
#         if isinstance(clf, sklearn.naive_bayes.BernoulliNB):
#             # Cateogrize integer variables (ndep_kid, ndep_old) into 0, 1, 2+ groups
#             # Categorize decimal variables into binary columns of tercile groups
#             num_cols = get_bool_num_cols(X)[1]
#             for c in num_cols:
#                 if c in ['ndep_kid', 'ndep_old']:
#                     for df in [X, Xa]:
#                         df['%s_0' % c] = (df[c] == 0).astype(int)
#                         df['%s_1' % c] = (df[c] == 1).astype(int)
#                         df['%s_2' % c] = (df[c] >= 2).astype(int)
#                         del df[c]
#                 else:
#                     wq1, wq2 = get_wquantile(X[c], w, 1/3), get_wquantile(X[c], w, 2/3)
#                     for df in [X, Xa]:
#                         df['%s_ter1' % c] = (df[c] < wq1).astype(int)
#                         df['%s_ter2' % c] = ((df[c] >= wq1) & (df[c] < wq2)).astype(int)
#                         df['%s_ter3' % c] = (df[c] >= wq2).astype(int)
#                         del df[c]
#         else:
#             pass
#
#         # Fit model
#         # Weight config for kNN is specified in clf input before fit. For all other clf weight is specified during fit
#         if isinstance(clf, sklearn.neighbors.KNeighborsClassifier):
#             f = lambda x: np.array([w]) # make sure weights[:, i] can be called in package code classification.py
#             clf = clf.__class__(weights=f)
#             clf = clf.fit(X, y)
#         else:
#             clf = clf.fit(X, y, sample_weight=w)
#
#         # Make prediction
#         if isinstance(clf, sklearn.linear_model.LinearRegression):
#             # simple OLS, get prediction directly
#             simcol = pd.Series(clf.predict(Xa), index=Xa.index)
#         else:
#             # probabilistic outcomes - get predicted probs, convert to df, assign target sample index for merging, assign col names
#             phat = get_pred_probs(clf, Xa)
#             phat = pd.DataFrame(phat).set_index(Xa.index)
#             phat.columns = ['p_%s' % int(x) for x in clf.classes_]
#             simcol = phat[phat.columns].apply(lambda x: simulate_wof(x), axis=1)
#
#         simcol.name = y.name
#         return simcol




clfs = ['random draw']
clfs += [sklearn.neighbors.KNeighborsClassifier(n_neighbors=5)]
clfs += [sklearn.neighbors.KNeighborsClassifier(n_neighbors=1)]
clfs += [sklearn.linear_model.LogisticRegression(solver='liblinear', multi_class='ovr')]
clfs += [sklearn.naive_bayes.MultinomialNB()]
clfs += [sklearn.ensemble.RandomForestClassifier()]
clfs += [sklearn.linear_model.RidgeClassifier()]

#clfs += [sklearn.svm.SVC(probability=True)]
#clfs += [sklearn.linear_model.SGDClassifier(loss='modified_huber', max_iter=1000, tol=0.001)]
#clfs = clfs[1:2]

D = d.copy()
outs = [] # list of results across iter times of test runs
for iter in range(1):
    random.seed(datetime.now())
    out = {} # a dict to store all results for all methods
    clf_names = [] # a list to store classifier names in output filename
    for clf in clfs:
        clf_name = ''
        if clf=='random draw':
            clf_name = 'randomDraw'
        elif isinstance(clf, sklearn.neighbors.KNeighborsClassifier):
            clf_name = clf.__class__.__name__
            clf_name += str(int(clf.get_params()['n_neighbors']))
        else:
            clf_name = clf.__class__.__name__
        clf_names.append(clf_name)


        print('Start running model. Method = %s' % clf_name)
        t0 = time()
        d = D.copy()

        ixs = list(d.index)
        random.shuffle(ixs)
        d = d.reindex(ixs)
        d = d.reset_index(drop=True)
        ixs_parts = []
        ixs_part_end = set(d.index) # initialize last partition - contains all unassigned rows in case mod(len(d), fold)!=0
        for kk in range(fold-1):
            ixs_part = d[(kk*part_size):((kk+1)*part_size)]['empid'].values
            ixs_parts.append(ixs_part)
            ixs_part_end = ixs_part_end - set(ixs_part)
        ixs_parts.append(np.array([x for x in ixs_part_end]))
        d = D.copy() # restore d as original

        ds = pd.DataFrame([]) # initialize df to store imputed results
        for kk in range(fold):
            ixs_ts = ixs_parts[kk]
            ixs_tr = np.array([x for x in set(d.index) - set(ixs_ts)])

            col_Xs, col_ys, col_w = get_columns()
            X = d.loc[ixs_tr, col_Xs]
            w = d.loc[X.index, col_w]
            Xa = d.loc[ixs_ts, col_Xs] # a fixed set of predictors for testing sample
            dkk = d.loc[ixs_ts, :].drop(columns=col_ys) # all cols but col_ys of train sample in d to store imputed values
            for c in col_ys:
                y = d.loc[ixs_tr, c]
                dkk = dkk.join(get_sim_col(X, y, w, Xa, clf))
            # Post-simluation logic control
            dkk.loc[dkk['male'] == 1, 'take_matdis'] = 0
            dkk.loc[dkk['male'] == 1, 'need_matdis'] = 0
            dkk.loc[(dkk['nevermarried'] == 1) | (dkk['divorced'] == 1), 'take_illspouse'] = 0
            dkk.loc[(dkk['nevermarried'] == 1) | (dkk['divorced'] == 1), 'need_illspouse'] = 0
            dkk.loc[dkk['nochildren'] == 1, 'take_bond'] = 0
            dkk.loc[dkk['nochildren'] == 1, 'need_bond'] = 0
            dkk.loc[dkk['nochildren'] == 1, 'take_matdis'] = 0
            dkk.loc[dkk['nochildren'] == 1, 'need_matdis'] = 0

            # Conditional simulation - anypay, doctor, hospital for taker/needer sample
            dkk['taker'] = dkk[['take_%s' % t for t in types]].apply(lambda x: max(x), axis=1)
            dkk['needer'] = dkk[['need_%s' % t for t in types]].apply(lambda x: max(x), axis=1)

            X = d.loc[ixs_tr, :]
            X = X[(X['taker'] == 1) | (X['needer'] == 1)][col_Xs]
            w = d.loc[X.index][col_w]
            Xa = dkk[(dkk['taker'] == 1) | (dkk['needer'] == 1)][col_Xs]

            if len(Xa) == 0:
                pass
            else:
                for c in ['anypay', 'doctor', 'hospital']:
                    y = d.loc[X.index][c]
                    dkk = dkk.drop(columns=[c])
                    dkk = dkk.join(get_sim_col(X, y, w, Xa, clf))
                # Post-simluation logic control
                dkk.loc[dkk['hospital'] == 1, 'doctor'] = 1

            # Conditional simulation - prop_pay for anypay=1 sample
            X = d.loc[ixs_tr, :]
            X = X[(X['anypay'] == 1) & (X['prop_pay'].notna())][col_Xs]
            w = d.loc[X.index][col_w]
            Xa = dkk[dkk['anypay'] == 1][X.columns]

            # a dict from prop_pay int category to numerical prop_pay value
            # int category used for phat 'p_0', etc. in get_sim_col
            v = d.prop_pay.value_counts().sort_index().index
            k = range(len(v))
            d_prop = dict(zip(k, v))
            D_prop = dict(zip(v, k))

            if len(Xa) == 0:
                pass
            else:
                y = d.loc[X.index]['prop_pay'].apply(lambda x: D_prop[x])
                dkk = dkk.drop(columns=['prop_pay'])
                yhat = get_sim_col(X, y, w, Xa, clf)
                # prop_pay labels are from 1 to 6, sklearn classes_ gives 0 to 5, increase label by 1
                if clf_name!='randomDraw':
                    yhat = pd.Series(data=yhat.values+1, index=yhat.index, name='prop_pay')
                dkk = dkk.join(yhat)
                dkk.loc[dkk['prop_pay'].notna(), 'prop_pay'] = dkk.loc[dkk['prop_pay'].notna(), 'prop_pay'].apply(
                    lambda x: d_prop[x])

            ds = ds.append(dkk)
        # leaves taken of each worker
        ds = ds.drop(columns=['num_leaves_taken'])
        ds['num_leaves_taken'] = ds[['take_%s' % t for t in types]].apply(lambda x: sum(x), axis=1)
        # prop_pay = 0 if nan in d or ds
        ds.loc[ds['prop_pay'].isna(), 'prop_pay'] = 0
        d.loc[d['prop_pay'].isna(), 'prop_pay'] = 0
        # Compute performance metrics - apply weights as necessary

        row = {}
        wcol = 'weight'
        rpw_cols = ['rpl%s' % "{0:0=2d}".format(x) for x in range(1, 81)]
        # Aggregate level metrics
        # total number of leave takers
        # total number of leaves taken
        # total number of leave needers
        # prop_pay - mean
        vcols = ['taker', 'num_leaves_taken', 'needer', 'prop_pay']
        for vcol in vcols:
            if vcol!='prop_pay':
                mean, spread = get_mean_spread(ds, vcol, wcol, rpw_cols, how='sum')
            else:
                mean, spread = get_mean_spread(ds, vcol, wcol, rpw_cols, how='mean')
            ci_lower, ci_upper = mean - spread, mean + spread
            row[vcol] = {}
            row[vcol]['mean'] = mean
            row[vcol]['ci_lower'] = ci_lower
            row[vcol]['ci_upper'] = ci_upper

        # Individual level metrics
        # accuracy - taker
        # accuracy - needer
        # accuracy - prop_pay
        row['accuracy'] = {}
        ds = ds.rename(columns={'taker':'taker_sim','needer':'needer_sim','prop_pay':'prop_pay_sim'})
        for vcol in ['taker', 'needer', 'prop_pay']:
            if vcol=='prop_pay':
                # restore prop_pay = nan if 0 in d or ds
                # prop_pay is conditional - don't inflate metric with out-of-universe 0s
                # np.nan==np.nan will give False and not counted in num of acc metric
                ds.loc[ds['%s_sim' % vcol]==0, '%s_sim' % vcol] = np.nan
                d.loc[d[vcol]==0, vcol] = np.nan
            vv = pd.DataFrame(ds['%s_sim' % vcol]).join(d[vcol])
            acc = (vv['%s_sim' % vcol]==vv[vcol]).value_counts()[True] / len(vv)
            row['accuracy'][vcol] = acc

        # store row in out
        out[clf_name] = row
        print('method %s results stored in out. TElapsed = %s' % (clf_name, (time() - t0)))

    # Simplify classfier names in out
    clf_names_short = ['random',
                       'KNN_multi',
                       'KNN1',
                       'logit',
                       'Naive Bayes',
                       'random_forest',
                       'ridge_class']
    dn = dict(zip(clf_names, clf_names_short))
    for k, v in dn.items():
        out[v] = out.pop(k)

    # send a copy of out to outs
    outs.append(out.copy())
    print('Test simulation completed for iter run %s' % iter)
    print('-------------------------------------------------------------')

# Get average values across out's
OUT = {}
for k, v in outs[0].items():
        OUT[k] = {} # set structure across method
        for k1, v1 in v.items():
            OUT[k][k1] = {} # set structure across var or acc
            for k2, v2 in v1.items():
                OUT[k][k1][k2] = np.nan
for k, v in OUT.items():
    for k1, v1 in v.items():
        for k2, v2 in v1.items():
            v2 = 0
            for dct in outs:
                v2 += dct[k][k1][k2]/len(outs) # build v2 value for OUT
            OUT[k][k1][k2] = v2 # assign V2 value to OUT leaves

out = OUT.copy()

# save as json
jsn = json.dumps(out)
f = open('./output/test_within_fmla_results_all.json', 'w')
f.write(jsn)
f.close()

# # Read json
# with open('./output/test_within_fmla_results_all.json') as f:
#     outr = json.load(f)
# out['logit'] # results before saving to json
# outr['logit'] # results read from saved json


# Plots
# Aggregate measures
vars = ['taker','needer','num_leaves_taken', 'prop_pay']
txts = ['Actual Leave Takers: ',
        'Actual Leave Needers: ',
        'Actual Leaves Taken: ',
        'Actual Prop Pay Mean: ']
dtxt = dict(zip(vars, txts))
for var in vars:
    if var!='prop_pay':
        y_label = 'million'
        y_red = (d[var]*d['weight']).sum()/10**6
        text_red = '%s%s %s' % (dtxt[var], round(y_red, 1), y_label)
        ys = [out[x][var]['mean'] / 10 ** 6 for x in out.keys()]
        es = [0.5 * (out[x][var]['ci_upper'] - out[x][var]['ci_lower']) / 10 ** 6 for x in out.keys()]
    else:
        y_label = 'Proportion of Pay Received from Employer (%)'
        y_red = (d[var] * d['weight'] / d['weight'].sum()).sum()/10**(-2)
        text_red = '%s%s%%' % (dtxt[var], round(y_red, 1))
        ys = [out[x][var]['mean']/10**(-2) for x in out.keys()]
        es = [0.5 * (out[x][var]['ci_upper'] - out[x][var]['ci_lower'])/10**(-2) for x in out.keys()]

    N = len(clfs)
    inds = [dn[k] for k in clf_names]
    width = 0.5
    fig, ax = plt.subplots(figsize=(8.7, 5))
    ax.bar(inds, ys, width, yerr=es, align='center', capsize=5, color='khaki')
    ax.set_ylabel(y_label)
    ax.set_xticklabels(inds)
    ax.yaxis.grid(False)
    #plt.xticks(rotation=22)
    plt.axhline(y=y_red, color='r', linestyle='--')
    plt.text(2, y_red * 1.1, text_red, horizontalalignment='center', color='r')
    plt.savefig('./output/figs/test_within_fmla_agg_%s' % (var),bbox_inches='tight')
    plt.show()

# Individual measures
vars = ['taker', 'needer', 'prop_pay']
txts = ['Random Accuracy: ',
        'Random Accuracy: ',
        'Random Accuracy: ']
dtxt = dict(zip(vars, txts))
for var in vars:
    y_label = 'Percent'
    y_red = out['random']['accuracy'][var]*10**2
    text_red = '%s%s%%' % (dtxt[var], round(y_red, 1))
    ys = [out[x]['accuracy'][var] *10 ** 2 for x in out.keys() if x!='random']

    N = len(ys)
    inds = [dn[k] for k in clf_names[1:]] # drop first: randomDraw - now the benchmark
    width = 0.5
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(inds, ys, width, align='center', capsize=5, color='khaki')
    ax.set_ylabel(y_label)
    ax.set_xticklabels(inds)
    ax.yaxis.grid(False)
    plt.axhline(y=y_red, color='r', linestyle='--')
    plt.text(2, y_red * 1.1, text_red, horizontalalignment='center', color='r')
    plt.savefig('./output/figs/test_within_fmla_indiv_%s' % (var))
    plt.show()

# ## Other factors
# # Leave prob factors, 6 types - TODO: code in wof in get_sim_col(), bound phat by max = 1
