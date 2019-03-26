# Source Python code for microsimulation model

This repository contains the code for the microsimulation project

_1_clean_FMLA.py cleans FMLA data, using no other auxiliary data sources  
_1a_impute_FMLA_CPS.py adds imputed FMLA variables based on CPS imputation  
_1c_get_length_distribution.py compute distribution of leave lengths based on FMLA data. Distribution is computed by state-benefit   receiving status, then by leave type  
_4_clean_ACS.py cleans ACS data for a given state, and a given year (ending year of 5-year ACS)  
_5_simulation.py is the main simulation engine. It simulates all intermediate and final variables for ACS workers in a chosen state. It then computes total program costs and cost breakdown by leave type.  
_5a_aux_functions.py contains all needed functions for data cleaning, simulation, etc.  
_test_total_cost.py tests model by simulating total program cost for CA/NJ/RI, given approximate program paratemers and cost data in these states  
_test_within_fmla.py performs cross validation using FMLA data only to check performance of different simulatino methods. Currently considering Accuracy measure as it considers both TP and TN cases.  

