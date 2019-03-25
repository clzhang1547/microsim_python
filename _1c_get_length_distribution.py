'''
compute empirical leave length distribution for 6 leave types,
separately for PFL states (using FMLA workers receiving any state pay)
and non-PFL states (using FMLA workers receiving no state pay)

chris zhang 2/28/2019
'''
import pandas as pd
import json

# Read in cleaned FMLA data
d = pd.read_csv('./data/fmla_2012/fmla_clean_2012.csv')

# A dictionary to store results
dct = {}
types = ['own', 'matdis', 'bond', 'illchild', 'illspouse', 'illparent']
# For PFL states
dct_PFL = {}
for t in types:
    xps = d[(d['recStatePay']==1) & (d['take_type']==t)][['weight', 'length']].groupby('length').sum()
    xps = (xps / xps.sum()).sort_index()
    xps.columns=['']
    xps = [(i, v.values[0]) for i, v in xps.iterrows()]
    dct_PFL[t] = xps
dct['PFL'] = dct_PFL
# For non-PFL states
dct_NPFL = {}
for t in types:
    xps = d[(d['recStatePay']==0) & (d['take_type']==t)][['weight', 'length']].groupby('length').sum()
    xps = (xps / xps.sum()).sort_index()
    xps.columns=['']
    xps = [(i, v.values[0]) for i, v in xps.iterrows()]
    dct_NPFL[t] = xps
dct['non-PFL'] = dct_NPFL

# Save as json
jsn = json.dumps(dct)
f = open('./data/fmla_2012/length_distributions.json', 'w')
f.write(jsn)
f.close()

'''
# Test read json
with open('length_distribution.json') as f:
    dctn = json.load(f)
dct['PFL']['matdis'] # results before saving to json
dctn['PFL']['matdis'] # results read from saved json
'''

