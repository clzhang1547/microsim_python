'''
main simulation engine

chris zhang 3/4/2019
'''
import pandas as pd
import numpy as np
import bisect
import json
from time import time
from _5a_aux_functions import *
import sklearn.linear_model, sklearn.naive_bayes, sklearn.neighbors, sklearn.tree, sklearn.ensemble, \
    sklearn.gaussian_process, sklearn.svm
import math
from datetime import datetime

# Read in cleaned ACS and FMLA data, and FMLA-based length distribution
st = 'ri'
yr = 16
pfl = 'non-PFL' # status of PFL as of ACS sample period
d = pd.read_csv('./data/fmla_2012/fmla_clean_2012.csv')
acs = pd.read_csv('./data/acs/ACS_cleaned_forsimulation_20%s_%s.csv' % (yr, st))
with open('./data/fmla_2012/length_distributions.json') as f:
    flen = json.load(f)

clf = sklearn.linear_model.LogisticRegression(solver='liblinear')
# clf = sklearn.ensemble.RandomForestClassifier()
# clf = sklearn.linear_model.RidgeClassifier()
# clf = sklearn.svm.SVC(probability=True)
# clf = sklearn.linear_model.SGDClassifier(loss='modified_huber', max_iter=1000, tol=0.001)
# clf = sklearn.neighbors.KNeighborsClassifier()
# clf = sklearn.naive_bayes.MultinomialNB()

# Train models using FMLA, and simulate on ACS workers
t0 = time()
col_Xs, col_ys, col_w = get_columns()
X = d[col_Xs]
w = d[col_w]
Xa = acs[X.columns]

for c in col_ys:
    tt = time()
    y = d[c]
    acs = acs.join(get_sim_col(X, y, w, Xa, clf))
    print('Simulation of col %s done. Time elapsed = %s' % (c, (time()-tt)))
print('6+6+1 simulated. Time elapsed = %s' % (time()-t0))

# Post-simluation logic control
acs.loc[acs['male']==1, 'take_matdis']=0
acs.loc[acs['male']==1, 'need_matdis']=0
acs.loc[(acs['nevermarried']==1) | (acs['divorced']==1), 'take_illspouse'] = 0
acs.loc[(acs['nevermarried']==1) | (acs['divorced']==1), 'need_illspouse'] = 0
acs.loc[acs['nochildren']==1, 'take_bond'] = 0
acs.loc[acs['nochildren']==1, 'need_bond'] = 0
acs.loc[acs['nochildren']==1, 'take_matdis'] = 0
acs.loc[acs['nochildren']==1, 'need_matdis'] = 0

# Conditional simulation - anypay, doctor, hospital for taker/needer sample
types = ['own', 'matdis', 'bond', 'illchild', 'illspouse', 'illparent']
acs['taker'] = acs[['take_%s' % t for t in types]].apply(lambda x: max(x), axis=1)
acs['needer'] = acs[['need_%s' % t for t in types]].apply(lambda x: max(x), axis=1)

X = d[(d['taker']==1) | (d['needer']==1)][col_Xs]
w = d.loc[X.index][col_w]
Xa = acs[(acs['taker']==1) | (acs['needer']==1)][X.columns]
if len(Xa)==0:
    pass
else:
    for c in ['anypay', 'doctor', 'hospital']:
        y = d.loc[X.index][c]
        acs = acs.join(get_sim_col(X, y, w, Xa, clf))
    # Post-simluation logic control
    acs.loc[acs['hospital']==1, 'doctor'] = 1

# Conditional simulation - prop_pay for anypay=1 sample
X = d[(d['anypay']==1) & (d['prop_pay'].notna())][col_Xs]
w = d.loc[X.index][col_w]
Xa = acs[acs['anypay']==1][X.columns]
# a dict from prop_pay int category to numerical prop_pay value
# int category used for phat 'p_0', etc. in get_sim_col
v = d.prop_pay.value_counts().sort_index().index
k = range(len(v))
d_prop = dict(zip(k, v))
D_prop = dict(zip(v, k))

if len(Xa)==0:
    pass
else:
    y = d.loc[X.index]['prop_pay'].apply(lambda x: D_prop[x])
    yhat = get_sim_col(X, y, w, Xa, clf)
    # prop_pay labels are from 1 to 6, get_sim_col() vectorization sum gives 0~5, increase label by 1
    yhat = pd.Series(data=yhat.values + 1, index=yhat.index, name='prop_pay')
    acs = acs.join(yhat)
    acs.loc[acs['prop_pay'].notna(), 'prop_pay'] = acs.loc[acs['prop_pay'].notna(), 'prop_pay'].apply(lambda x: d_prop[x])

# Draw leave length for each type
# Without-program lengths - draw from FMLA-based distribution (pfl indicator = 0)
# note: here, cumsum/bisect is 20% faster than np/choice.
# But when simulate_wof applied as lambda to df, np/multinomial is 5X faster!
t0 = time()
for t in types:
    acs['len_%s' % t] = 0
    n_lensim = len(acs.loc[acs['take_%s' % t]==1]) # number of acs workers who need length simulation
    print(n_lensim)
    ps = [x[1] for x in flen[pfl][t]] # prob vector of length of type t
    cs = np.cumsum(ps)
    lens = [] # initiate list of lengths
    for i in range(n_lensim):
        lens.append(flen[pfl][t][bisect.bisect(cs, np.random.random())][0])
    acs.loc[acs['take_%s' % t]==1, 'len_%s' % t] = np.array(lens)
    print('mean = %s' % acs['len_%s' % t].mean())
print('te: sq length sim = %s' % (time()-t0))

# Max needed lengths (mnl) - draw from simulated without-program length distribution
# conditional on max length >= without-program length
T0 = time()
for t in types:
    t0 = time()
    acs['mnl_%s' % t] = 0
    # resp_len = 0 workers' mnl = sq length
    acs.loc[acs['resp_len']==0, 'mnl_%s' % t] = acs.loc[acs['resp_len']==0, 'len_%s' % t]
    # resp_len = 1 workers' mnl draw from length distribution conditional on new length > sq length
    dct_vw = {} # dict from sq length to possible greater length value, and associated weight of worker who provides the length
    x_max = acs['len_%s' % t].max()
    for x in acs['len_%s' % t].value_counts().index:
        if x<x_max:
            dct_vw[x] = acs[(acs['len_%s' % t] > x)][['len_%s' % t, 'PWGTP']].groupby(by='len_%s' % t)['PWGTP'].sum().reset_index()
            mx = len(acs[(acs['resp_len'] == 1) & (acs['len_%s' % t] == x)])
            vxs = np.random.choice(dct_vw[x]['len_%s' % t], mx, p=dct_vw[x]['PWGTP'] / dct_vw[x]['PWGTP'].sum())
            acs.loc[(acs['resp_len']==1) & (acs['len_%s' % t]==x), 'mnl_%s' % t] = vxs
        else:
            acs.loc[(acs['resp_len']==1) & (acs['len_%s' % t]==x), 'mnl_%s' % t] = x*1.25
    print('mean = %s. MNL sim done for type %s. telapse = %s' % (acs['mnl_%s' % t].mean(), t, (time()-t0)))

# logic control of mnl
acs.loc[acs['male']==1, 'mnl_matdis']=0
acs.loc[(acs['nevermarried']==1) | (acs['divorced']==1), 'mnl_illspouse'] = 0
acs.loc[acs['nochildren']==1, 'mnl_bond'] = 0
acs.loc[acs['nochildren']==1, 'mnl_matdis'] = 0

print('All MNL sim done. TElapsed = %s' % (time()-T0))

# Compute program cost
elig_wage12 = 3440
elig_wkswork = 20
elig_yrhours = 1
elig_empsizebin = 1
rrp = 0.67
wkbene_cap = 650
d_maxwk = dict(zip(types, 6*np.ones(6)))
d_takeup = dict(zip(types, 1*np.ones(6)))
incl_empgov = False
incl_empself = False

# get individual cost
# sample restriction
acs = acs.drop(acs[(acs['taker']==0) & (acs['needer']==0)].index)

if not incl_empgov:
    acs = acs.drop(acs[(acs['empgov_fed']==1) | (acs['empgov_st']==1) | (acs['empgov_loc']==1)].index)
if not incl_empself:
    acs = acs.drop(acs[(acs['COW']==6) | (acs['COW']==7)].index)

# program eligibility - TODO: port to GUI input, program eligibility determinants
acs['elig_prog'] = 0
acs.loc[(acs['wage12']>=elig_wage12) &
        (acs['wkswork']>=elig_wkswork) &
        (acs['wkswork']*acs['wkhours']>=elig_yrhours) &
        (acs['empsize']>=elig_empsizebin), 'elig_prog'] = 1

acs = acs.drop(acs[acs['elig_prog']!=1].index)

# daily wage
acs['wage1d'] = 8 * acs['wage12'] / (acs['wkswork'] * acs['wkhours'])

# leave length as function of replacement ratio
# assumption: if employer pay equal or higher, use indefinitely. If prog pay higher, use up to max period.
# at current rr = prop_pay, leave length = status-quo (sql), at 100% rr, leave length = max needed length (mnl)
# at proposed prog rr = rrp, if rrp> (1-prop_pay), then leave length = mnl. Leave length covered by program = mnl - sql
# OW, linearly interpolate at rr = (prop_pay + rrp). Leave length covered by program = (mnl - sql)*rrp/(1-prop_pay)

# cpl: covered-by-program leave length, 6 types
acs.loc[acs['prop_pay'].isna(), 'prop_pay'] = 0

for t in types:
    acs['cpl_%s' % t] = 0
    acs.loc[acs['prop_pay'] < rrp, 'cpl_%s' % t] = \
        acs['len_%s' % t] + (acs['mnl_%s' % t] - acs['len_%s' % t]) * (rrp - acs['prop_pay'])/ (1-acs['prop_pay'])
    acs['cpl_%s' % t] = acs['cpl_%s' % t].apply(lambda x: math.ceil(x))
    # apply max number of covered weeks
    acs['cpl_%s' % t] = acs['cpl_%s' % t].apply(lambda x: min(x, d_maxwk[t]*5))

# apply take up rates and weekly benefit cap, and compute total cost, 6 types
costs = {}
for t in types:
    v = (acs['cpl_%s' % t]/5) * (5 * acs['wage1d'] * rrp).apply(lambda x: min(x, wkbene_cap))
    w = acs['PWGTP']*d_takeup[t]
    costs[t] = (v*w).sum()
costs['total'] = sum(list(costs.values()))
# compute standard error using replication weights, then compute confidence interval
sesq = dict(zip(costs.keys(), [0]*len(costs.keys())))
for wt in ['PWGTP%s' % x for x in range(1, 81)]:
    costs1 = {}
    for t in types:
        v = (acs['cpl_%s' % t]/5) * (5 * acs['wage1d'] * rrp).apply(lambda x: min(x, wkbene_cap))
        w = acs[wt]*d_takeup[t]
        costs1[t] = (v*w).sum()
    costs1['total'] = sum(list(costs1.values()))
    for k in costs1.keys():
        sesq[k] += 4/80 * (costs[k] - costs1[k])**2
for k, v in sesq.items():
    sesq[k] = v**0.5
ci = {}
for k, v in sesq.items():
    ci[k] = (costs[k] - 1.96*sesq[k], costs[k] + 1.96*sesq[k])



# Save output
out_costs = pd.DataFrame.from_dict(costs, orient='index')
out_costs = out_costs.reset_index()
out_costs.columns = ['type', 'cost']

out_ci = pd.DataFrame.from_dict(ci, orient='index')
out_ci = out_ci.reset_index()
out_ci.columns = ['type', 'ci_lower', 'ci_upper']

out = pd.merge(out_costs, out_ci, how='left', on='type')

d_tix = {'own':1, 'matdis':2, 'bond':3, 'illchild':4, 'illspouse':5, 'illparent':6, 'total':7}
out['tix'] = out['type'].apply(lambda x: d_tix[x])
out = out.sort_values(by='tix')
del out['tix']
out_id = datetime.now().strftime('%Y%m%d_%H%M%S')
out.to_csv('./output/program_cost_%s_%s.csv' % (st, out_id), index=False)

# Plot costs and ci
out['cost'].hist()
out['ci_lower'].hist()
out['ci_upper'].hist()
print('Output saved. Total cost = $%s million 2012 dollars' % (round(costs['total']/1000000, 1)) )

## Other factors
# Leave prob factors, 6 types - TODO: code in wof in get_sim_col(), bound phat by max = 1
