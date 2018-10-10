'''
Simulate leave taking behavior of ACS sample, using FMLA data

to do:
1. Need to think more about imputation to fill in missing values before kNN
2. Need to impute coveligd, more from ACM model
3. Need to compute counterfactual 'length' of leave for FMLA samples under new program

Chris Zhang 9/13/2018
'''

# -------------
# Housekeeping
# -------------

import pandas as pd
import numpy as np
import random
import os.path
from _1a_get_response import get_response
from _5a_simulators import simulate_knn
from time import time
from datetime import datetime

class SimulationEngine():
    def __init__(self, st, fp_acs, fp_fmla_cf, fp_out, rr1, hrs, d_max_wk, max_wk_replace):
        '''

        :param st: state name, 'ca', 'ma', etc.
        :param fp_acs: file path to cleaned up state-level ACS data
        :param fp_fmla_cf: file path to cleaned up FMLA data, with counterfactual leave vars generated
        :param fp_out: file path to save output
        :param rr1: replacement rate under new program
        :param hrs: min annual work hours for eligibility
        :param d_max_wk: a dict from leave type to max number of weeks to receive benefits
        :param max_wk_replace: max weekly benefits

        Returns: None
        '''


        self.st = st
        self.fp_acs = fp_acs
        self.fp_fmla_cf = fp_fmla_cf
        self.fp_out = fp_out
        self.rr1 = rr1
        self.hrs = hrs
        self.d_max_wk = d_max_wk
        self.max_wk_replace = max_wk_replace
        
        # a dict from varname style leave types to user-readable leave types
        self.d_type = {}
        self.d_type['own'] = 'Own Health'
        self.d_type['matdis'] = 'Maternity'
        self.d_type['bond'] = 'New Child'
        self.d_type['illchild'] = 'Ill Child'
        self.d_type['illspouse'] = 'Ill Spouse'
        self.d_type['illparent'] = 'Ill Parent'

    def get_simulator_params(self):
        Xs = ['age', 'male', 'employed', 'wkhours', 'noHSdegree',
                  'BAplus', 'empgov_fed', 'empgov_st', 'empgov_loc',
                  'lnfaminc', 'black', 'asian', 'hisp', 'other',
                  'ndep_kid', 'ndep_old', 'nevermarried', 'partner',
                  'widowed', 'divorced', 'separated']
        k = 2
        return (Xs, k)

    def get_acs_simulated(self):
        t0 = time()
        # -------------
        # Read in Parameters
        # -------------

        # Algorithm parameter
        Xs, k = self.get_simulator_params()

        # -------------
        # Load Data
        # -------------

        # Read in the ACS data for the specified state
        acs = pd.read_csv(self.fp_acs)

        # -------------
        # Read or Simulate Counterfactual Leaves
        # -------------

        # Read fmla_clean_2012_resp_length.csv, the FMLA dataset with predicted counterfactual length of leave
        # if no such file, create from fmla_clean_2012.csv
        outname=self.fp_fmla_cf
        if not os.path.isfile(outname):
            get_response(outname = outname)
        fmla = pd.read_csv(outname)

        # Simulate the predicted counterfactual length of leave in the ACS based
        # on the value for the k nearest neighbors in the FMLA
        vars = ['length','resp_length',
                'type1_own','type1_matdis', 'type1_bond',
                'type1_illchild','type1_illspouse','type1_illparent']
        acs[vars] = simulate_knn(k, fmla, acs, Xs, vars)

        # -------------
        # Restrict ACS sample
        # -------------

        # Restrict based on employment status and age
        acs = acs[(acs.age>=18)]
        acs = acs.drop(index=acs[acs.ESR==4].index) # armed forces at work
        acs = acs.drop(index=acs[acs.ESR==5].index) # armed forces with job but not at work
        acs = acs.drop(index=acs[acs.ESR==6].index) # NILF
        acs = acs.drop(index=acs[acs.COW==6].index) # self-employed, not incorporated
        acs = acs.drop(index=acs[acs.COW==7].index) # self-employed, incoporated
        acs = acs.drop(index=acs[acs.COW==8].index) # working without pay in family biz
        acs = acs.drop(index=acs[acs.COW==9].index) # unemployed for 5+ years, or never worked

        # Compute FMLA eligibility
        acs['coveligd'] = 0

        # set to 1 for all gov workers
        acs.loc[acs['empgov_fed']==1, 'coveligd'] = 1
        acs.loc[acs['empgov_st']==1, 'coveligd'] = 1
        acs.loc[acs['empgov_loc']==1, 'coveligd'] = 1

        # set to 1 for all workers with annual hours >= hrs
        acs['yrhours'] = acs['wkhours'] * acs['wks']
        acs.loc[acs['yrhours']>=self.hrs, 'coveligd'] = 1
        del acs['yrhours']

        # check wm-eligibility against FMLA
        coveligd_wm_acs = sum(acs['coveligd']*acs['PWGTP']) / sum(acs['PWGTP'])
        coveligd_wm_fmla = (fmla['coveligd']*fmla['freq_weight']).sum() / fmla[fmla.coveligd.isna()==False]['freq_weight'].sum()
        x = coveligd_wm_acs/coveligd_wm_fmla
        print('Estimated mean eligibility in ACS = %s times of mean eligibility in FMLA data' % round(x, 3))

        # -------------
        # Compute statistics based on the simulated variables above
        # -------------

        # daily wage
        acs['wage1d'] = acs['wage12'] / acs['wks'] / 5
        acs.loc[acs['wage12']==0, 'wage1d'] = 0 # hopefully this solves all missing wage1d cases
        t1 = time()
        print('Simulation done for all ACS workers in state %s. Time elapsed = %s seconds' % (self.st.upper(), (t1-t0)))
        return acs

    def get_sq_paras(self):
        '''
        :return: status-quo program parameters, now set as an average replacement rate
        '''
        if self.st == 'ca':
            return 0.55
        else:
            return 0
        
    def get_cost(self, acs, d_takeups, alpha=0.911, counterfactual=True):
        '''

        :param acs: acs with all leave vars simulated (sourced) from FMLA data
        :param d_takeups: a dict from leave type to takeup rates
        :param rr1: proposed replacement rate
        :param alpha: calibration factor to account for adjustment in eligibility, employer payment, take-up, etc.
                    Hardcoded for now based on CA PFL data
        :param counterfactual: if False then will compute cost using status-quo 'length' in acs instead of 'resp_length'
        :return:
        '''
        # leave types
        types = ['own', 'matdis', 'bond', 'illchild','illspouse', 'illparent']

        # set parameters for Status-quo / Counterfactual scenarios
        rr0 = self.get_sq_paras()
        if counterfactual:
            rr = self.rr1
            col_length = 'resp_length'
            status = 'Counterfactual'
        else:
            rr = rr0
            col_length = 'length'
            status = 'Status-quo'
        # set rr0=status-quo replacement rate, so that (rr-rr0)/(1-rr0)=share of rr increase out of total possible increase
        # Adjust full responsive leave length to replacement rate
        # assume full responsive leave length would result under rr = 100%
        acs['resp_length'] = acs[['length', 'resp_length']].apply(lambda x: x[0] + (x[1]-x[0])*(self.rr1-rr0)/(1-rr0), axis=1)
        # Compute total program cost
            # compute eligible leave length in work weeks
            # breakdown by leave type, and apply leave length cap of each type
        acs['len_wks'] = acs[col_length] / 5  # length in work weeks
        for type in types:
            acs['len_wks_%s' % type] = acs['len_wks'] * acs['type1_%s' % type] # len_wks weighted by decimal type1_%s
            acs['len_wks_%s' % type] = acs['len_wks_%s' % type].apply(lambda x: min(x, self.d_max_wk[type]))
        acs['len_wks'] = acs[['type1_%s' % x for x in types]].apply(lambda x: sum(x), axis=1) # set len_wks as sum of
                                                                                        # capped type-specific len_wks
            # compute weekly eligible replacement in dollars
        acs['replace1w'] = acs['wage1d'] * rr * 5
        acs['replace1w'] = acs['replace1w'].apply(lambda x: min(x, self.max_wk_replace))
            # Make a pd.Series of total cost, and breakdown across 6 leave types
        acs['alpha'] = alpha
                # cost_all = total cost if takeup = 1
        acs['cost_all'] = acs['len_wks'] * acs['replace1w'] * acs['PWGTP'] * acs['coveligd'] * acs['alpha']
        TCs = []  # initiate an output list of total program costs
        for type in types:
            acs['cost_%s' % type] = acs['cost_all'] * acs['type1_%s' % type]
            TCs.append(round(sum(acs['cost_%s' % type])/10**6, 3)*d_takeups[type]) # type-level takeup handled here
        TCs = [sum(TCs)] + TCs
        TCs = pd.Series(TCs, index= ['Total'] + [self.d_type[type] for type in types])
        TCs_out = TCs[:] # keep a copy of TCs in pd.Series format as output
        print('State = %s, Replacement rate = %s, Status = %s, Total Program Cost = $%s million' % (self.st, rr, status, round(TCs['Total'], 1)))
            # Make a pd.Series of user input
        user_input = pd.Series([])
        user_input['State'] = self.st.upper()
        if counterfactual:
            user_input['Presence of New Program'] = 'Yes'
        else:
            user_input['Presence of New Program'] = 'No'
            user_input['Eligibility Requirement, Minimum Hours Worked'] = self.hrs
            user_input['Replacement Rate'] = rr
        for type in types:
            user_input['Maximum Weeks to Receive Benefit, %s' % self.d_type[type]] = self.d_max_wk[type]
        user_input['Weekly Benefit Cap'] = self.max_wk_replace
        for type in types:
            user_input['Takeup Rate, %s' % self.d_type[type]] = d_takeups[type]
            # Save a output file with user input and total cost combined
        user_input = user_input.reset_index()
        user_input.columns = ['User Input', 'Value']
        TCs = TCs.reset_index()
        TCs.columns = ['Leave Type', 'Program Cost, $ Millions']
        out = user_input.join(TCs)
        now = datetime.now()
        out_id = now.strftime('%Y%m%d%H%M%S')
        out.to_csv(self.fp_out + '/program_cost_%s_%s.csv' % (self.st, out_id), index=False)
        print('Simulation output saved to %s' % self.fp_out)
        return TCs_out