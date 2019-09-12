'''
partition ACS PUMS by state of work

chris zhang 9/11/2019
'''

import pandas as pd
from time import time
import os.path
## Initialize
#  a DataFrame to store person rows with missing state of work
dm = pd.DataFrame([])
# a dict - mapping state code [st] to df of persons with POWSP==st
dct_pow = {}
# a df to store person rows with pow = overseas code
d_overseas = pd.DataFrame([])

## Read in data
# # read a few rows for testing
# reader = pd.read_csv("./data/csv_pus/ss16pusa.csv", iterator=True)
# d = reader.get_chunk(10**3)

# read by chunk
chunksize = 10 ** 6
for part in ['a', 'b', 'c', 'd']:
    dct_pow[part] = {}
    ichunk = 0
    for d in pd.read_csv('./data/csv_pus/ss16pus%s.csv' % part, chunksize=chunksize):
        ichunk += 1
        t0_chunk = time()
        n_dm_0 = len(dm) # n rows in dm before sending any rows in current chunk
        n_sent_0 = 0
        for st in dct_pow[part].keys():
            n_sent_0 += len(dct_pow[part][st]) # n rows in dct_pow[st] across st, before sending any rows in current chunk
        # reduce sample to civilian employed (ESR=1/2)
        # and have paid work (COW=1/2/3/4/5), including self-employed(COW=6/7)
        d = d[((d['ESR'] == 1) | (d['ESR'] == 2)) &
              ((d['COW'] == 1) | (d['COW'] == 2) | (d['COW'] == 3) | (d['COW'] == 4) | (d['COW'] == 5) |
               (d['COW'] == 6) | (d['COW'] == 7))]

        # send rows with missing pow to dm
        dm = dm.append(d[d['POWSP'].isna()])
        # send rows with pow=st to dct_pow[st]
        t0 = time()
        for st in set(d[~d['POWSP'].isna()]['POWSP']):
            if st in dct_pow[part].keys():
                dct_pow[part][st] = dct_pow[part][st].append(d[d['POWSP']==st])
            else:
                dct_pow[part][st] = d[d['POWSP']==st]
        t1 = time()
        print('All person rows in current chunk sent to dct_pow[st]. '
              'Time needed for this chunk = %s' % round((t1-t0), 0))

        # in current chunk , check if total number of rows sent is equal to that of original file
        n = 0
        for st in dct_pow[part].keys():
            n += len(dct_pow[part][st]) # total number of rows sent so far in current part
        print('Number of person rows with valid POWSP that sent in current chunk = %s' % (n - n_sent_0))
        print('Number of person rows with missing POWSP that sent in current chunk = %s' % (len(dm) - n_dm_0))
        print('Number of person rows of current chunk (ESR=1/2, COW=1~7) = %s, ' % len(d),
              'number of rows not sent = %s' % (len(d)- (n - n_sent_0) - (len(dm) - n_dm_0)))
        t1_chunk = time()
        print('--------------------------------------------------------')
        print('Chunk %s of US file part %s processed' % (ichunk, part),
              '\n Time needed = %s seconds' % round((t1_chunk - t0_chunk), 0))
        print('--------------------------------------------------------')

## Save files

# a dict from state fips to state abbrev
st_fips = pd.read_excel('./data/state_fips.xlsx')
dct_st = dict(zip(st_fips['st'], st_fips['state_abbrev']))
# ensure st fips is integer in dct_pow[part]
for part in dct_pow.keys():
    dct_pow[part] = {int(k): v for k, v in dct_pow[part].items()}
# save files for each st fips of each part
for part in dct_pow.keys():
    for st in dct_pow[part].keys():
        if st in dct_st.keys(): # st might be code for overseas pow
            dct_pow[part][st].to_csv('./output/pow_by_state_part/p%s_%s_pow_part_%s.csv' % ('0'*(2-len(str(st)))+str(st), dct_st[st].lower(), part), index=False)
            print('Output csv saved for st = %s in part = %s. Now saving the next file...' % (part, st))
        else:
            d_overseas = d_overseas.append(dct_pow[part][st])
d_overseas.to_csv('./output/p_pow_overseas.csv', index=False)
dm.to_csv('./output/p_pow_missing.csv', index=False)
print('Done - all files saved.')

## For each st, combine parts (a~d) if file of that part is available

for st in dct_st.keys():
    t0 = time()
    df = pd.DataFrame([])
    for part in ['a', 'b', 'c', 'd']:
        fp = './output/p%s_%s_pow_part_%s.csv' % ('0'*(2-len(str(st)))+str(st), dct_st[st].lower(), part)
        if os.path.isfile(fp):
            df = df.append(pd.read_csv(fp))
    if len(df)>0:
        df.to_csv('./output/pow_by_state/person_files/p%s_%s_pow.csv' % ('0'*(2-len(str(st)))+str(st), dct_st[st].lower()))
    t1 = time()
    print('File combining (a~d) finished for state %s. Time needed = %s seconds.' % (dct_st[st], round((t1-t0),0)))
