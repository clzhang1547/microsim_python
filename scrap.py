import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
X = [[0], [1], [2], [3]]
y = [0, 1, 2, 3]

X = pd.DataFrame(X)
y = pd.DataFrame(y)

def get_ws(ds):
    ws = ds ** 0.5
    return ws

neigh = KNeighborsRegressor(n_neighbors=2, weights=lambda x: x**0.5)
neigh.fit(X, y) 
print(neigh.predict([[1.5], [2.8]]))
yjh = neigh.predict([[1.5], [2.8]])
yjh = pd.DataFrame(yjh)

#############################

cols = ['age', 'agesq', 'male', 'employed',
        'wkhours', 'noHSdegree', 'BAplus',
        'empgov_fed', 'empgov_st', 'empgov_loc',
        'lnfaminc', 'black', 'asian', 'hisp', 'other',
        'ndep_kid', 'ndep_old',
        'nevermarried', 'partner', 'widowed', 'divorced', 'separated']

for c in fmla_xtrf.columns:
    print('Col = %s --------' % c)
    try:
        print(fmla_xtrf[c].isna().value_counts()[True])
    except:
        IndexError

#########################

import pandas as pd
import numpy as np
import sklearn.linear_model

fmla = pd.read_csv('./data/fmla_2012/fmla_clean_2012_resp_length.csv')
fmla['ones'] = np.ones(len(fmla))
fmla.index.name = 'empid'
acs = pd.read_csv('./data/acs/ACS_cleaned_forsimulation_ma.csv')
acs['ones'] = np.ones(len(acs))
acs = acs[(acs.age >= 18)]
acs = acs.drop(index=acs[acs.ESR == 4].index)  # armed forces at work
acs = acs.drop(index=acs[acs.ESR == 5].index)  # armed forces with job but not at work
acs = acs.drop(index=acs[acs.ESR == 6].index)  # NILF
acs = acs.drop(index=acs[acs.COW == 6].index)  # self-employed, not incorporated
acs = acs.drop(index=acs[acs.COW == 7].index)  # self-employed, incoporated
acs = acs.drop(index=acs[acs.COW == 8].index)  # working without pay in family biz
acs = acs.drop(index=acs[acs.COW == 9].index)  # unemployed for 5+ years, or never worked
acs.index.name = 'acswid'

def test(Xs, yones=False):
    ys = ['taker', 'needer']
    ys += ['resp_len']
    w = ['fixed_weight']

    ixs_tr = np.random.choice(fmla.index, int(0.8 * len(fmla)), replace=False)
    fmla_xtr = fmla.loc[ixs_tr][Xs]
    fmla_ytr = fmla.loc[ixs_tr][ys]
    wght = fmla.loc[ixs_tr][w]
    wght = [x[0] for x in np.array(wght)]

    # ACS columns for simulation
    acs_x = acs[Xs]

    # Fill in missing values
    fmla_xtr = fmla_xtr.fillna(fmla_xtr.mean())
    fmla_ytr = fmla_ytr.fillna(0)  # fill with label 0 for now
    acs_x = acs_x.fillna(acs_x.mean())

    # Fit the training data and predict taker/needer/resp_len for ACS
    clf = sklearn.linear_model.LogisticRegression()
    for c in fmla_ytr.columns:
        clf.fit(fmla_xtr, fmla_ytr[c], sample_weight=wght)
        # acs[c] = np.rint(clf.predict(acs_x))
        acs[c] = clf.predict_proba(acs_x)

    if yones==True:
        fmla_ytr = [np.random.choice([0,1], 1)[0] for x in range(len(fmla_xtr))]
        fmla_ytr = np.array(fmla_ytr)
        clf.fit(fmla_xtr, fmla_ytr, sample_weight=wght)
        acs['z'] = clf.predict_proba(acs_x)
        print(acs.z.value_counts())
        print(fmla_ytr.mean())
        coef = [round(x, 3) for x in clf.coef_[0]]
        db = dict(zip(Xs, coef ))
        db = pd.DataFrame.from_dict(db, orient='index')
        print(db)

    if yones==False:
        return acs[['taker','needer','resp_len']]
    else:
        return acs['z']




Xs = ['age', 'agesq', 'male',
      'black', 'asian', 'hisp', 'other',
      'nevermarried', 'partner','widowed', 'divorced', 'separated',
      'noHSdegree','BAplus',
      'empgov_fed', 'empgov_st', 'empgov_loc',
      'lnfaminc',
      'ndep_kid', 'ndep_old']
# Xs = ['ones']
yhat = test(Xs, yones=False)

for c in ['taker','needer','resp_len']:
    yhat['z_%s' % c] = yhat[c].apply(lambda x: np.rint(x))

ixs_tr = np.random.choice(fmla.index, int(0.8 * len(fmla)), replace=False)
fmla_xtr = fmla.loc[ixs_tr][Xs]
acs_x = acs[Xs]
# Fill in missing values
fmla_xtr = fmla_xtr.fillna(fmla_xtr.mean())
acs_x = acs_x.fillna(acs_x.mean())
for x in Xs:
    print('X = %s, FMLA------- ' % x)
    print(round(fmla[x].mean(), 3))
    print('X = %s, ACS-------' % x)
    print(round(acs[x].mean(), 3))
    print('##################################')

############################

Xs = ['age', 'agesq', 'male',
      'black', 'asian', 'hisp', 'other',
      'nevermarried', 'partner','widowed', 'divorced', 'separated',
      'noHSdegree','BAplus',
      'empgov_fed', 'empgov_st', 'empgov_loc',
      'lnfaminc',
      'ndep_kid', 'ndep_old']

from time import time
n = 10000
## wheel of fortune

ps = [0.91, 0.04, 0.05]
y = []
t0 = time()
for x in range(n):
    z = np.random.uniform()
    ix = simulate_wof(ps, z)
    y.append(ix)
y = np.array(y)
print('Mean of y = %s' % y.mean())
print('Time elapsed = %s' % (time()-t0))
print('------------------------------------')
## np.random.multinomial
t0 = time()
ym = np.random.multinomial(1, ps, n)
ym = list(ym)
ym = [list(x) for x in ym]
ymix = [x.index(1) for x in ym]
ymix = np.array(ymix)
print('Mean of ymix = %s' % ymix.mean())
print('Time elapsed = %s' % (time()-t0))

ks = otypes
vs = [6]*len(ks)
d_max_wk = dict(zip(ks, vs))
d_clf={}
d_clf['Logistic Regression'] = sklearn.linear_model.LogisticRegression()
d_clf['Ridge Classifier'] = sklearn.linear_model.RidgeClassifier()
d_clf['Stochastic Gradient Descent'] = sklearn.linear_model.SGDClassifier()
d_clf['K Nearest Neighbor'] = sklearn.neighbors.KNeighborsClassifier()
d_clf['Naive Bayes'] = sklearn.naive_bayes.MultinomialNB()
d_clf['Support Vector Machine'] = sklearn.svm.SVC()
d_clf['Random Forest'] = sklearn.ensemble.RandomForestClassifier()


def fit_model(xtr, ytr, ws):
    '''
    fit model using a simulatino method, with some configurations tailored to the method
    :param xtr: training data, x
    :param ytr: training data, y
    :param ws: weights

    '''
    clf_name = 'K Nearest Neighbor'
    clf = sklearn.neighbors.KNeighborsClassifier
    if clf_name in ['Logistic Regression',
                         'Random Forest',
                         'Support Vector Machine',
                         'Ridge Classifier',
                         'Stochastic Gradient Descent',
                         'Naive Bayes']:
        clf.fit(xtr, ytr, sample_weight=ws)
    if clf_name in ['K Nearest Neighbor']:
        f = lambda x: ws
        clf = sklearn.neighbors.KNeighborsClassifier(weights=f)
        clf.fit(xtr, ytr)

    return clf



X = [[0], [1], [2], [3]]
y = [0, 0, 1, 1]
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import SGDClassifier
clf = SGDClassifier()

c = 'type_recent'
# c = 'taker'
ytr = fmla.loc[ixs_tr]
ytr = ytr[(ytr['LEAVE_CAT'] != 3) & (ytr['type_recent'].notna())][c]
xtr = fmla_xtr.loc[ytr.index]  # use indices of ytr to pick xtr rows
wght = fmla.loc[ytr.index][w]
wght = [x[0] for x in np.array(wght)]

clf.fit(xtr, ytr, sample_weight = wght)
d = clf.decision_function(acs_x) # distance to hyperplane
d = np.array(d)
d = np.sign(d) * np.minimum(100, abs(d)) # bound the exponents to +-100
phat = np.exp(d) / np.array([[x]*len(d[0]) for x in np.exp(d).sum(axis=1)])


phat = np.exp(d) / (1 + np.exp(d)) # list of pr(yhat = 1)
phat = np.array([[(1-x), x] for x in phat])


wght = np.array([wght])
f = lambda x: wght
clf = sklearn.neighbors.KNeighborsClassifier(weights=f)
clf.fit(fmla_xtr, fmla_ytr[c])
x = clf.predict_proba(acs_x)

'''
FutureWarning: max_iter and tol parameters have been added in <class 'sklearn.linear_model.stochastic_gradient.SGDClassifier'> in 0.19.
If both are left unset, they default to max_iter=5 and tol=None.
If tol is not None, max_iter defaults to max_iter=1000. From 0.21, default max_iter will be 1000, and default tol will be 1e-3.
  "and default tol will be 1e-3." % type(self), FutureWarning)
'''

cps = pd.read_csv('./data/cps/CPS2014extract.csv')