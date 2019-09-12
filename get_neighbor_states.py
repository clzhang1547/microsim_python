'''
get neighbor states for each state

chris zhang 9/11/2019
'''
import geopandas as gpd
import pandas as pd
pd.set_option('max_colwidth', 100)
pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 200)
from time import time
import json

# read in shape file
states = gpd.read_file('./data/shp/state/tl_2017_us_state.shp')

# a dict from FIPS code to state abbrev
# a dict the other way around
dct_fips = dict(zip(states['STATEFP'], states['STUSPS']))
dct_fips_r = dict(zip(states['STUSPS'], states['STATEFP']))

# get neighbors - send (code, state abbrev) tuple to dct_neighbor[(code state)]
dct_neighbor = {}
for i, row in states.iterrows():
    t0 = time()
    # get codes of 'not disjoint' states
    codes_neighbors = list(states[~states['geometry'].disjoint(row['geometry'])]['STATEFP'])
    # remove own code from the list
    codes_neighbors = [code for code in codes_neighbors if row['STATEFP'] != code]
    # send codes of neighbors to dict
    dct_neighbor[row['STATEFP']] = [(code, dct_fips[code]) for code in codes_neighbors]
    t1 = time()
    print('Neighbor states sent to dct_neighbor for state %s (%s). Time needed = %s seconds.'
          % (dct_fips[row['STATEFP']], row['STATEFP'], round((t1-t0), 0)))

# add in 'semi-neighbor' states where driving is possible own and neighbor
# so such 'semi-neighbor' state of work is considered possible
dct_semi_neighbors = {
    'DC': ['DE', 'NJ', 'NY', 'PA', 'WV'],
    'DE': ['DC', 'NY'],
    'NJ': ['DC'],
    'NY': ['DC', 'DE'],
    'PA': ['DC'],
    'WV': ['DC'],
    'CT': ['ME', 'NH', 'VT'],
    'MA': ['ME'],
    'RI': ['VT', 'NH', 'ME'],
    'VT': ['CT', 'ME', 'RI'],
    'RI': ['NH', 'VT', 'ME'],
    'ME': ['CT', 'VT', 'MA', 'RI']
}
for k, vs in dct_semi_neighbors.items():
    for v in vs:
        dct_neighbor.update({dct_fips_r[k]: dct_neighbor[dct_fips_r[k]] + [(dct_fips_r[v], v)]})

# save dct_neighbor as json
with open('./output/neighbor_states.json', 'w') as f:
    json.dump(dct_neighbor, f, indent=4)
