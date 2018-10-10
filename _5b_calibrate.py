'''
Calibrate microsimulation model parameters

1. Calibrate a parameter that captures link between replacement rate and average leave length, use CA data

Chris Zhang 10/3/2018
'''

from _5_simulation_engine import SimulationEngine
import numpy as np

# Set up
types = ['own', 'matdis', 'bond', 'illchild', 'illspouse','illparent']
st = 'ca'
fp_acs = './data/acs/ACS_cleaned_forsimulation_%s.csv' % st
fp_fmla_cf = './data/fmla_2012/fmla_clean_2012_resp_length.csv'
fp_out = './output'
rr1 = 0.25 # set at any value in calibration, only relevant if counterfactual=True in se.get_cost()
hrs = 1250
d_max_wk = dict(zip(types, 6*np.ones(6))) # set as max week in CA
max_wk_replace = 1216 # set as CA weekly benefit cap
se = SimulationEngine(st, fp_acs, fp_fmla_cf, fp_out, rr1, hrs, d_max_wk, max_wk_replace)
acs = se.get_acs_simulated()

# Status-quo estimated cost, CA
takeups = dict(zip(types, 1*np.ones(6))) # set as 1 for now, 40% for matdis in CA per
                                         # http://poverty.ucdavis.edu/sites/main/files/file-attachments/cpr-pihl_basso_pfl_brief.pdf
if st=='ca':
      cost0 = se.get_cost(acs,takeups,1,counterfactual=False)['Total'] # to get non-calibrated cost0, set alpha = 1
      # Status-quo empirical cost, CA
      cost0_emp = 5513 + 864  # CA FY17-18 total DI + PFL,
                              # https://www.edd.ca.gov/about_edd/pdf/qspfl_PFL_Program_Statistics.pdf
                              # https: // www.edd.ca.gov / about_edd / pdf / qsdi_DI_Program_Statistics.pdf
      alpha = round(cost0_emp / cost0, 3) # calibration factor to account for adjustment in eligibility, employer payment, take-up, etc.
      print('Calibration factor alpha = %s needs to be multiplied to program cost estimate based on CA PFL' % alpha)


##### compute example counterfactual program costs
# TCs = se.get_cost(acs, takeups)
# print(TCs)