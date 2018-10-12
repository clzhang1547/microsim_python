
# """
# This program loads in the raw ACS files, creates the necessary variables
# for the simulation and saves a master dataset to be used in the simulations.
# 
# This is replicating the counterpart file in from Python
# 
# 9 Sept 2018
# Luke
# last update by Chris Zhang 10/11/2018, validated all cols against Python ACS cleaning code output, except following cols:
# weeks_worked, paid_hrly, emp_size, as these are from CPS-based imputation. Need to check the separate imputation code later.
# 
# """

# -------------------------- #
# ACS Household File
# -------------------------- #
clean_acs <-function(person_csv,house_csv,csv=FALSE, filename) {


  d <-read.csv(person_csv)
  d_hh <-read.csv(house_csv)
  d_cps <- read.csv("C:/workfiles/Microsimulation/git/large_data_files/CPS2014extract.csv")
  
  # create variables
  
  d_hh$nochildren <- as.data.frame(dummy("FPARC",d_hh))$FPARC4
    # adjust to 2012 dollars to conform with FMLA 2012 data
    # don't multiple ADJINC directly to faminc to avoid integer overflow issue in R
  d_hh$adjinc_2012 <- d_hh$ADJINC / 1042852 
  d_hh$faminc <- d_hh$FINCP * d_hh$adjinc_2012 
  d_hh <- d_hh %>% mutate(faminc=ifelse(is.na(faminc)==FALSE & faminc<=0, 0.01, faminc)) # force non-positive income to be epsilon to get meaningful log-income
  d_hh$lnfaminc <- log(d_hh$faminc)
  
  # number of dependents
  d_hh$ndep_kid <- d_hh$NOC
  d_hh$ndep_old <- d_hh$R65
  
   
  # -------------------------- #
  # ACS Person File
  # -------------------------- #
  
  # load file
  #d <- read.csv("ss15pma_short.csv")
  #d <- read.csv("ss16pca.csv")
  #d <- read.csv("ss15pma.csv")
  
  
  # merge with household level vars 
  d <- merge(d,d_hh[c("SERIALNO","nochildren","lnfaminc","faminc", "PARTNER","ndep_kid","ndep_old")], by="SERIALNO")
  
  # rename ACS vars to be consistent with FMLA data
  d$age <- d$AGEP
  d$a_age <- d$AGEP
  
  # create new ACS vars
  
  
  # marital status
  d$married <- as.data.frame(dummy("MAR",d))$MAR1
  d$widowed <- as.data.frame(dummy("MAR",d))$MAR2
  d$divorced <- as.data.frame(dummy("MAR",d))$MAR3
  d$separated <- as.data.frame(dummy("MAR",d))$MAR4
  d$nevermarried <- as.data.frame(dummy("MAR",d))$MAR5
    # use PARTNER in household data to tease out unmarried partners
  d <- d %>% mutate(PARTNER=ifelse(is.na(PARTNER),0,PARTNER)) 
  d <- d %>% mutate(partner=ifelse(PARTNER==1 | PARTNER==2 | PARTNER==3 | PARTNER==4, 1, 0))
  d <- d %>% mutate(married=ifelse(partner==1, 0, married))
  d <- d %>% mutate(widowed=ifelse(partner==1, 0, widowed))
  d <- d %>% mutate(divorced=ifelse(partner==1, 0, divorced))
  d <- d %>% mutate(separated=ifelse(partner==1, 0, separated))
  d <- d %>% mutate(nevermarried=ifelse(partner==1, 0, nevermarried))
  
  #gender
  d$male <- as.data.frame(dummy("SEX",d))$SEX1
  d$female <- 1-d$male
  
  #age
  d$agesq <- d$age ** 2
  
  # ed level
  d <- d %>% mutate(SCHL=ifelse(is.na(SCHL),0,SCHL)) 
  d <- d %>% mutate(ltHS=ifelse(SCHL<=11,1,0))
  d <- d %>% mutate(someHS=ifelse(SCHL>=12 & SCHL<=15,1,0)) 
  d <- d %>% mutate(HSgrad=ifelse(SCHL>=16 & SCHL<=17,1,0)) 
  d <- d %>% mutate(someCol=ifelse(SCHL>=18 & SCHL<=20,1,0)) 
  d <- d %>% mutate(BA =ifelse(SCHL==21,1,0)) 
  d <- d %>% mutate(GradSch=ifelse(SCHL>=22,1,0))
    # coarser ed groups
  d <- d %>% mutate(noHSdegree=ifelse(SCHL<=15,1,0))
  d <- d %>% mutate(BAplus=ifelse(SCHL>=21,1,0))
  
    
  #race
  d <- d %>% mutate(hisp=ifelse(HISP>=2,1,0)) 
  d <- d %>% mutate(black=ifelse(RAC1P==2 & hisp==0,1,0)) 
  d <- d %>% mutate(white=ifelse(RAC1P==1 & hisp==0,1,0)) 
  d <- d %>% mutate(asian=ifelse(RAC1P==6 & hisp==0,1,0))
  d <- d %>% mutate(native=ifelse((RAC1P==3 | RAC1P==4 | RAC1P==5 | RAC1P==7) & hisp==0,1,0))
  d <- d %>% mutate(other=ifelse(white==0 & black==0 & asian==0 & native==0 & hisp==0,1,0))
  
  # Employement, and government employement
  d <- d %>% mutate(employed=ifelse(ESR==1 | ESR==2 | ESR==4 | ESR==5, 1, 0))
  d <- d %>% mutate(employed=ifelse(is.na(ESR)==TRUE, NA, employed))
  d <- d %>% mutate(empgov_fed=ifelse(COW==5, 1, 0))
  d <- d %>% mutate(empgov_fed=ifelse(is.na(COW)==TRUE, NA, empgov_fed))
  d <- d %>% mutate(empgov_st=ifelse(COW==4, 1, 0))
  d <- d %>% mutate(empgov_st=ifelse(is.na(COW)==TRUE, NA, empgov_st))  
  d <- d %>% mutate(empgov_loc=ifelse(COW==3, 1, 0))
  d <- d %>% mutate(empgov_loc=ifelse(is.na(COW)==TRUE, NA, empgov_loc))
  
  # occupation
  # different years of ACS code occupation under different names
    # convert occ codes from factor format to numeric codes
  d <- d %>% mutate(OCCP10 = as.numeric(as.character(OCCP10)))
  d <- d %>% mutate(OCCP12 = as.numeric(as.character(OCCP12)))
    # new col OCCP tries to use OCCP12, if unavailable then use OCCP10
  d$OCCP <- NA
  d <- d %>% mutate(OCCP = ifelse(is.na(OCCP12)==FALSE, OCCP12, OCCP))
  d <- d %>% mutate(OCCP = ifelse(is.na(OCCP)==TRUE & is.na(OCCP12)==TRUE & is.na(OCCP10)==FALSE, OCCP10, OCCP))  
  
  d <- d %>% mutate(occ_1 = ifelse(OCCP>=10 & OCCP<=950,1,0),
                      occ_2 = ifelse(OCCP>=1000 & OCCP<=3540,1,0),
                      occ_3 = ifelse(OCCP>=3600 & OCCP<=4650,1,0),
                      occ_4 = ifelse(OCCP>=4700 & OCCP<=4965,1,0),
                      occ_5 = ifelse(OCCP>=5000 & OCCP<=5940,1,0),
                      occ_6 = ifelse(OCCP>=6000 & OCCP<=6130,1,0),
                      occ_7 = ifelse(OCCP>=6200 & OCCP<=6940,1,0),
                      occ_8 = ifelse(OCCP>=7000 & OCCP<=7630,1,0),
                      occ_9 = ifelse(OCCP>=7700 & OCCP<=8965,1,0),
                      occ_10 = ifelse(OCCP>=9000 & OCCP<=9750,1,0))
  
  # industry
  d <- d %>% mutate(  ind_1 = ifelse(INDP>=170 & INDP<=290 ,1,0),
                      ind_2 = ifelse(INDP>=370 & INDP<=490 ,1,0),
                      ind_3 = ifelse(INDP==770 ,1,0),
                      ind_4 = ifelse(INDP>=1070 & INDP<=3990 ,1,0),
                      ind_5 = ifelse(INDP>=4070 & INDP<=5790 ,1,0),
                      ind_6 = ifelse((INDP>=6070 & INDP<=6390) |(INDP>=570 & INDP<=690), 1,0),
                      ind_7 = ifelse((INDP>=6470 & INDP<=6780) ,1,0),
                      ind_8 = ifelse(INDP>=6870 & INDP<=7190 ,1,0),
                      ind_9 = ifelse(INDP>=7270 & INDP<=7790 ,1,0),
                      ind_10 = ifelse(INDP>=7860 & INDP<=8470 ,1,0),
                      ind_11 = ifelse(INDP>=8560 & INDP<=8690 ,1,0),
                      ind_12 = ifelse(INDP>=8770 & INDP<=9290 ,1,0),
                      ind_13 = ifelse(INDP>=9370 & INDP<=9590 ,1,0))
  
  # Hours per week
  d$wkhours <- d$WKHP
  
  # Weeks worked
  # simply taking midpoint of range for now
  # Haven't had success implementing an ordinal regression in R that's consistent with ACM 
  
  d <- d %>% mutate(weeks_worked=ifelse(WKW==1,51,0))
  d <- d %>% mutate(weeks_worked=ifelse(WKW==2,48.5,weeks_worked))
  d <- d %>% mutate(weeks_worked=ifelse(WKW==3,43.5,weeks_worked))
  d <- d %>% mutate(weeks_worked=ifelse(WKW==4,33,weeks_worked))
  d <- d %>% mutate(weeks_worked=ifelse(WKW==5,20,weeks_worked))
  d <- d %>% mutate(weeks_worked=ifelse(WKW==6,7.0,weeks_worked))
  d <- d %>% mutate(weeks_worked=ifelse(is.na(weeks_worked),0,weeks_worked))
  
  # Health Insurance from employer
  d <- d %>% mutate(hiemp=ifelse(HINS1==1,1,0))
  
  # earnings over past 12m, and log earnings
  #d$adjinc_2012 <- d$ADJINC / 1042852
  d <- d %>% mutate(wage12=WAGP*(ADJINC/1042852))
  d <- d %>% mutate(lnearn=ifelse(wage12>0, log(wage12), NA))
  
  # presence of children
  d <- d %>% mutate(fem_cu6= ifelse(PAOC==1,1,0))
  d <- d %>% mutate(fem_c617= ifelse(PAOC==2,1,0))
  d <- d %>% mutate(fem_cu6and617= ifelse(PAOC==3,1,0))
  d <- d %>% mutate(fem_nochild= ifelse(PAOC==4,1,0))
  
  
  # -------------------------- #
  # Remove ineligible workers
  # -------------------------- #
  
  # Restrict dataset to civilian employed workers (check this)
  # d <- subset(d, ESR==1|ESR==2)
  
  #  Restrict dataset to those that are not self-employed and not gov't workers
  # d <- subset(d, COW<=3 | COW>=7)
  
  # strip to only required variables to save memory
  d <- d[c("nochildren", "lnfaminc", "faminc", "wage12","lnearn","hiemp","fem_cu6","fem_c617","fem_cu6and617","fem_nochild","ndep_kid","ndep_old", 
           "a_age","age", "widowed", "divorced","married","separated", "nevermarried","partner",
           "male", "female", "agesq", "ltHS", "someHS","HSgrad", "someCol","BA", 
           "GradSch", "noHSdegree","BAplus","black", "white", "asian", "native","other", "hisp", "OCCP", "occ_1", "occ_2", "occ_3", 
           "occ_4", "occ_5", "occ_6", "occ_7", "occ_8", "occ_9", "occ_10", "ind_1", "ind_2", "ind_3", "ind_4", 
           "ind_5", "ind_6", "ind_7", "ind_8", "ind_9", "ind_10", "ind_11", "ind_12", "ind_13",
           "employed","empgov_fed","empgov_st","empgov_loc",
           "wkhours","weeks_worked",
           "WAGP","WKHP","PWGTP","FER", "WKW")]
  
  #============================================
  # Impute variables from CPS
  #============================================
  # id variable
  d$empid <- as.numeric(rownames(d))
  d <- d[order(d$empid),]
  
  # load imputation functions 
  source("1a.estimate_behavioral_CPS.R")
  d <- CPS_impute(d, d_cps)
  
  # -------------------------- #
  # Save the resulting dataset
  # -------------------------- #
  
  
  if (csv==TRUE) {
    write.csv(d, file = filename, row.names = FALSE)  
  }
  return(d)
}

##############################
#person_csv = "C:/workfiles/Microsimulation/git/large_data_files/ss15pma.csv"
#house_csv = "C:/workfiles/Microsimulation/git/large_data_files/ss15hma.csv"
#filename = "ACS_clean_ma.csv"
#clean_acs(person_csv, house_csv, TRUE, filename)

#outfile = read.csv("ACS_clean_ma.csv")