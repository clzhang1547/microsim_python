'''
Take cleaned up FMLA and impute some variables using CPS data

Chris Zhang 11/19/2018
'''
import pandas as pd
import numpy as np
import sklearn.linear_model
import mord
import math
from _5a_aux_functions import fillna_binary
from time import time

t0 = time()
# Read in and clean data
d = pd.read_csv('./data/fmla_2012/fmla_clean_2012.csv')
cps = pd.read_csv('./data/cps/CPS2014extract.csv')

cps['female']=np.where(cps['a_sex']==2, 1, 0)
cps['female']=np.where(cps['a_sex'].isna(), np.nan, cps['female'])
cps['black']=np.where(cps['prdtrace']==2, 1, 0)
cps['black']=np.where(cps['prdtrace'].isna(), np.nan, cps['black'])
cps['age']=cps['a_age']
cps['agesq']=cps['age']*cps['age']
cps['BA']=np.where(cps['a_hga']==43, 1, 0)
cps['BA']=np.where(cps['a_hga'].isna(), np.nan, cps['BA'])
cps['GradSch']=np.where((cps['a_hga']<=46) & (cps['a_hga']>=44), 1, 0)
cps['GradSch']=np.where(cps['a_hga'].isna(), np.nan, cps['GradSch'])
for i in cps['a_mjind'].value_counts().sort_index().index:
    cps['ind_%s' % i] = np.where(cps['a_mjind']==i, 1, 0)
    cps['ind_%s' % i] = np.where(cps['a_mjind'].isna(), np.nan, cps['ind_%s' % i])
for i in cps['a_mjocc'].value_counts().sort_index().index:
    cps['occ_%s' % i] = np.where(cps['a_mjocc']==i, 1, 0)
    cps['occ_%s' % i] = np.where(cps['a_mjocc'].isna(), np.nan, cps['occ_%s' % i])

cps['hourly'] = np.where(cps['a_hrlywk']==1, 1, 0)
cps['hourly'] = np.where((cps['a_hrlywk']==0) | (cps['a_hrlywk'].isna()), np.nan, cps['hourly'])
cps['empsize'] = cps['noemp']
cps['oneemp'] = np.where(cps['phmemprs']==1, 1, 0)
cps['oneemp'] = np.where(cps['phmemprs'].isna(), np.nan, cps['oneemp'])

cps = cps[['female', 'black', 'age', 'agesq', 'BA', 'GradSch'] +
          ['ind_%s' % x for x in range(1, 14)] +
          ['occ_%s' % x for x in range(1, 11)] +
          ['hourly', 'empsize','oneemp','wkswork','marsupwt']] # remove armed forces code from ind/occ
cps = cps.dropna(how='any')
'''
do logit below:
y: paid hourly, employer size, single employer last year, weeks worked (subject to FMLA weeks worked categories if any)
x: chars - female, black, age, agesq, BA, GradSch, all occ codes, all ind codes

'''


# logit regressions
X = cps[['female', 'black', 'age', 'agesq', 'BA', 'GradSch']]
w = cps['marsupwt']
Xd = fillna_binary(d[X.columns])
# cps based hourly paid indicator
y = cps['hourly']
clf = sklearn.linear_model.LogisticRegression(solver='liblinear').fit(X, y, sample_weight=w)
d['hourly_fmla'] = pd.Series(clf.predict(Xd))
# one employer last year
y = cps['oneemp']
clf = sklearn.linear_model.LogisticRegression(solver='liblinear').fit(X, y, sample_weight=w)
d['oneemp_fmla'] = pd.Series(clf.predict(Xd))
# ordered logit - TODO: mord package not ideal for handling empsize, cannot impute all 6 levels, best is LogisticAT().
# employer size
y = cps['empsize']
clf = mord.LogisticAT().fit(X, y)
d['empsize_fmla'] = pd.Series(clf.predict(Xd))
# regression
# weeks worked
y = cps['wkswork']
clf = sklearn.linear_model.LinearRegression().fit(X, y, sample_weight=w)
d['wkswork_fmla'] = pd.Series(clf.predict(Xd))


# Save files
d.to_csv("./data/fmla_2012/fmla_clean_2012.csv", index=False)
cps.to_csv("./data/cps/cps_for_acs_sim.csv", index=False)

print('CPS cleaned and CPS variable imputation done for FMLA. Time elapsed = %s seconds' % (round(time()-t0, 2)))