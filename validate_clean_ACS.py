'''
validate Python and R microsimulation code - clean_ACS

Python code version: demo files sent to Minh for review on 10/04/2018
R code version: Luke's GitHub commit 960baa0

Chris Zhang 10/10/2018
'''

import pandas as pd
import numpy as np

## Validate _4_clean_ACS.py and 2.clean_ACS.R
# local fp
fp_loc = 'C:/workfiles/Microsimulation/git'
st = 'ma'

# read raw data in case need them
ACS_p = pd.read_csv(fp_loc + '/large_data_files/ss15p%s.csv' % st)
ACS_hh = pd.read_csv(fp_loc + '/large_data_files/ss15h%s.csv' % st)

# read cleaned-up ACS data for one state
acsP = pd.read_csv(fp_loc + '/microsim_python/data/acs/ACS_cleaned_forsimulation_%s.csv' % st)
acsR = pd.read_csv(fp_loc + '/microsim_R-master/ACS_clean_%s.csv' % st)
AcsP = acsP[:]
AcsR = acsR[:] # copies of full acs

    # get original ACS cols, and rename them in acsP and acsR
    # do this for ACS person data only, as only a few cols in ACS hh data are used so no need to reduce
acsRaw = pd.read_csv(fp_loc + '/large_data_files/ss15p%s.csv' % st) # consider

cols_orig = list(acsRaw.columns)
d = dict(zip(cols_orig, ['o_' + c for c in cols_orig]))
acsP = acsP.rename(d, axis='columns')
acsR = acsR.rename(d, axis='columns')
acsP = acsP.drop([c for c in acsP.columns if c[:2]=='o_'], axis=1) # drop original cols
acsR = acsR.drop([c for c in acsR.columns if c[:2]=='o_'], axis=1) # drop original cols

# get difference in newly created cols
cols_Ponly = set(acsP.columns) - set(acsR.columns)
cols_Ronly = set(acsR.columns) - set(acsP.columns)
i = 0
print('------------\nPython only, columns of ACS_cleaned_forsimulation_%s.csv:' % st)
for c in cols_Ponly:
    i+=1
    print(i, c)

i = 0
print('------------\nR only, columns of ACS_clean_%s.csv:' % st)
for c in cols_Ronly:
    i+=1
    print(i, c)

# get difference in common cols
cols_PR = set(acsP.columns).intersection(set(acsR.columns))
dPR = pd.DataFrame([])
n = len(acsP)
for c in cols_PR:
    acsP[c] = acsP[c].apply(lambda x: round(x, 3))
    acsR[c] = acsR[c].apply(lambda x: round(x, 3)) # round up to compared decimals
    dPR[c] = (acsP[c] == acsR[c]) | ((acsP[c]!=acsP[c]) & (acsR[c]!=acsR[c]))
i = 0
for c in cols_PR:
    try:
        if dPR[c].value_counts()[True]!= n:
            i+=1
            print('%s-th Col different between P and R: %s' % (i, c))
    except KeyError:
        if dPR[c].value_counts()[False]>0:
            i += 1
            print('%s-th Col different between P and R: %s' % (i, c))

'''
# some code to examine rows/cols in at indices where discrepancy between P and R dfs occur

c='other'
vars = ['white','black','asian','native','hisp']
v = 1
ixsR = set(acsR[acsR[c]==v][vars].index)
ixsP = set(acsP[acsP[c]==v][vars].index)
ixs = ixsR - ixsP
print('-----P-----')
print(acsP.loc[ixs, vars + [c]].head(15))
print('-----R----')
print(acsR.loc[ixs, vars + [c]].head(15))


ACS_hh['faminc'] = ACS_hh['']
'''





