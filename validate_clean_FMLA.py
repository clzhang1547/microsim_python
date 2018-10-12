'''
validate Python and R microsimulation code - clean_FMLA

Python code version: demo files sent to Minh for review on 10/04/2018
R code version: Luke's GitHub commit 960baa0

Chris Zhang 10/8/2018
'''

import pandas as pd
import numpy as np

## Validate _1_clean_FMLA.py and 1.clean_FMLA.R
# local fp
fp_loc = 'C:/workfiles/Microsimulation/git'
# read cleaned-up FMLA data
fmlaP = pd.read_csv(fp_loc + '/microsim_python/data/fmla_2012/fmla_clean_2012.csv')
fmlaR = pd.read_csv(fp_loc + '/microsim_R-master/fmla_clean_2012.csv' )
FmlaP = fmlaP[:]
FmlaR = fmlaR[:] # copies of full fmla
    # get original FMLA cols, and rename them in fmlaP and fmlaR
fmlaRaw = pd.read_csv(fp_loc + '/microsim_python/data/fmla_2012/fmla_2012_employee_restrict_puf.csv' )
cols_orig = list(fmlaRaw.columns)
d = dict(zip(cols_orig, ['o_' + c for c in cols_orig]))
fmlaP = fmlaP.rename(d, axis='columns')
fmlaR = fmlaR.rename(d, axis='columns')
fmlaP = fmlaP.drop([c for c in fmlaP.columns if c[:2]=='o_'], axis=1) # drop original cols
fmlaR = fmlaR.drop([c for c in fmlaR.columns if c[:2]=='o_'], axis=1) # drop original cols

# get difference in newly created cols
cols_Ponly = set(fmlaP.columns) - set(fmlaR.columns)
cols_Ronly = set(fmlaR.columns) - set(fmlaP.columns)
i = 0
print('------------\nPython only, columns of fmla_clean_2012.csv:')
for c in cols_Ponly:
    i+=1
    print(i, c)

i = 0
print('------------\nR only, columns of fmla_clean_2012.csv:')
for c in cols_Ronly:
    i+=1
    print(i, c)

# get difference in common cols
cols_PR = set(fmlaP.columns).intersection(set(fmlaR.columns))
dPR = pd.DataFrame([])
n = len(fmlaP)
for c in cols_PR:
    fmlaP[c] = fmlaP[c].apply(lambda x: round(x, 3))
    fmlaR[c] = fmlaR[c].apply(lambda x: round(x, 3)) # round up to compared decimals like lnlength
    dPR[c] = (fmlaP[c] == fmlaR[c]) | ((fmlaP[c]!=fmlaP[c]) & (fmlaR[c]!=fmlaR[c]))
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

c='take_illspouse'
vars = ['reason_take','LEAVE_CAT']
v = 0
ixsR = set(FmlaR[fmlaR[c]==v][vars].index)
ixsP = set(FmlaP[fmlaP[c]==v][vars].index)
ixs = ixsP - ixsR
print('-----P-----')
print(FmlaP.loc[ixs, vars + [c]].head(15))
print('-----R----')
print(FmlaR.loc[ixs, vars + [c]].head(15))

'''








