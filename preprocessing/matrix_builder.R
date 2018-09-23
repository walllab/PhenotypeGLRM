########################################################################################
######################################### ADOS #########################################
########################################################################################

#### MODULE 1 AGGREGATION ####
AC.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/ADOS_Module_1.csv"
AC.df = df = read.csv(AC.file)
colnames(AC.df)

AC.df = AC.df[ which( ! AC.df$Subject.Id %in% c(NA, 'N/A', '')) , ]

AGRE.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADOS Mod1/ADOS11.csv"
AGRE.df = df = read.csv(AGRE.file)
colnames(AGRE.df)


svip1.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/ados_1.csv'
svip1.1 = df = read.csv(svip1.file)
svip1.1 = subset(svip1.1, ados_1.total >= 0)

svip2.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/ados_1.csv'
svip2.1 = df = read.csv(svip2.file)
svip2.1 = subset(svip2.1, ados_1.total >= 0)

SVIP.df = rbind(svip1.1, svip2.1)
colnames(SVIP.df)

SVIP2.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/svip_summary_variables.csv"
SVIP2.df = df = read.csv(SVIP2.file)
SVIP.gender = SVIP2.df[c('individual', 'svip_summary_variables.sex')]

SVIP.df = merge(SVIP.df, SVIP.gender, by = 'individual')

SSC.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ados_1_raw.csv"
SSC.df = df = read.csv(SSC.raw.file)
head(SSC.df)


SSC.twin.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_1_raw.csv"
SSC.twin.df = df = read.csv(SSC.twin.raw.file)
head(SSC.twin.df)


SSC.df = rbind(SSC.df, SSC.twin.df)
colnames(SSC.df)

SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv"
SSC2.df = df = read.csv(SSC.file)
SSC.age = SSC2.df[c('individual', 'age_at_ados', 'sex')]

SSC.df = merge(SSC.df, SSC.age)

AGP.file = "/scratch/PI/dpwall/DATA/phenotypes/AGP_pheno_all_201112/ados_mod_1.csv"
AGP.df = df = read.csv(AGP.file)
AGP.df$Subject.Id = paste(AGP.df$FID, AGP.df$IID, sep = "-")



items = c('A1','A2','A3','A4','A5','A6','A7','A8','B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11','B12','C1','C2','D1','D2','D3','D4','E1','E2','E3')
colnames(AC.df)[12:34] = items [1:23]; colnames(AC.df)[36] = 'D2'; colnames(AC.df)[38:39] = c('D3','D4'); colnames(AC.df)[41:43] = items[27:29]
colnames(SVIP.df)[7:35] = items
colnames(SSC.df)[3:31] = items
colnames(AGRE.df)[c(21:40,46:54)] = items
colnames(AGP.df)[5:33] = items


colnames(SVIP.df)[c(1,6)] = c('Subject.Id', 'age_months'); SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'male'] = 'M'; SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'female'] = 'F'
colnames(SSC.df)[c(1,32)] = c('Subject.Id', 'age_months'); SSC.df$gender[SSC.df$sex == 'male'] = 'M'; SSC.df$gender[SSC.df$sex == 'female'] = 'F'
colnames(AGRE.df)[7] = 'Subject.Id'; AGRE.df$age_months = AGRE.df$age*12; AGRE.df$gender[AGRE.df$Gender == 1] = 'M'; AGRE.df$gender[AGRE.df$Gender == 2] = 'F'; AGRE.df$gender = as.factor(AGRE.df$gender)
colnames(AC.df)[c(1,9,2)] = c('Subject.Id', 'age_months', 'gender')
colnames(AGP.df)[4] = 'age_months'; AGP.df$gender = NA

for(i in 5:33) {
  AGP.df[,i] <- as.numeric(AGP.df[,i])
}


myvars <- c('Subject.Id',items, 'age_months', 'gender')
AC.subset <- AC.df[myvars]
SVIP.subset <- SVIP.df[myvars]
AGRE.subset <- AGRE.df[myvars]
SSC.subset <- SSC.df[myvars]



m1.df = rbind(AC.subset, SVIP.subset, AGRE.subset, SSC.subset)


m1.df[,2:30][m1.df[,2:30] == '-1'] = 8
m1.df[,2:30][m1.df[,2:30] < 0] = 8
m1.df[,2:30][m1.df[,2:30] > 8] = 8


m1.recode = m1.df
m1.recode[,2:30][m1.recode[,2:30] < 0] = 8
m1.recode[,2:30][m1.recode[,2:30] >= 7] = 0
m1.recode[,2:30][m1.recode[,2:30] == 3] = 2


for (i in (1:length(m1.df$A1))){
  if (m1.df$A1[i] %in% c(3,4,8)){
    m1.df$social_affect_calc[i] = (m1.recode$A2[i] + m1.recode$A8[i] + m1.recode$B1[i] + m1.recode$B3[i] + m1.recode$B4[i] + m1.recode$B5[i] +
                                     m1.recode$B9[i] + m1.recode$B10[i] + m1.recode$B11[i] + m1.recode$B12[i])
    m1.df$restricted_repetitive_calc[i] = (m1.recode$A3[i] + m1.recode$D1[i] + m1.recode$D2[i] + m1.recode$D4[i])
    m1.df$SA_RRI_total_calc[i] = (m1.df$social_affect_calc[i] + m1.df$restricted_repetitive_calc[i])
    if (m1.df$age_months[i] < 36.0){
      if (m1.df$SA_RRI_total_calc[i] <= 6){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 8){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 13){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 15){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 22){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 24){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 25){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] < 48.0){
      if (m1.df$SA_RRI_total_calc[i] <= 6){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 8){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 14){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 15){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 20){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 22){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 23){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 24){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 25){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] < 72.0){
      if (m1.df$SA_RRI_total_calc[i] <= 3){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 6){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 12){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 15){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 23){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 25){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 26){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] >= 72.0){
      if (m1.df$SA_RRI_total_calc[i] <= 3){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 6){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 13){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 15){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 22){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 24){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 25){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 26){m1.df$severity_calc[i] = 10}
    }
    
  } else if (m1.df$A1[i] %in% c(1,2,0)){
    m1.df$social_affect_calc[i] = (m1.recode$A2[i] + m1.recode$A7[i] + m1.recode$A8[i] + m1.recode$B1[i] + m1.recode$B3[i] + m1.recode$B4[i] + m1.recode$B5[i] +
                                     m1.recode$B9[i] + m1.recode$B10[i] + m1.recode$B12[i])
    m1.df$restricted_repetitive_calc[i] = (m1.recode$A5[i] + m1.recode$D1[i] + m1.recode$D2[i] + m1.recode$D4[i])
    m1.df$SA_RRI_total_calc[i] = (m1.df$social_affect_calc[i] + m1.df$restricted_repetitive_calc[i])
    if (m1.df$age_months[i] < 36.0){
      if (m1.df$SA_RRI_total_calc[i] <= 3){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 5){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 7){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 11){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 13){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 16){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 22){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] < 48.0){
      if (m1.df$SA_RRI_total_calc[i] <= 4){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 6){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 7){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 9){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 11){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 14){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 17){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 22){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] < 60.0){
      if (m1.df$SA_RRI_total_calc[i] <= 2){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 4){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 7){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 9){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 11){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 15){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 18){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 20){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 22){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 23){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] < 84.0){
      if (m1.df$SA_RRI_total_calc[i] <= 2){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 4){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 7){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 10){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 11){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 16){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 19){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 23){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 24){m1.df$severity_calc[i] = 10}
    }
    else if (m1.df$age_months[i] >= 84.0){
      if (m1.df$SA_RRI_total_calc[i] <= 2){m1.df$severity_calc[i] = 1}
      else if (m1.df$SA_RRI_total_calc[i] <= 5){m1.df$severity_calc[i] = 2}
      else if (m1.df$SA_RRI_total_calc[i] <= 7){m1.df$severity_calc[i] = 3}
      else if (m1.df$SA_RRI_total_calc[i] <= 9){m1.df$severity_calc[i] = 4}
      else if (m1.df$SA_RRI_total_calc[i] <= 11){m1.df$severity_calc[i] = 5}
      else if (m1.df$SA_RRI_total_calc[i] <= 18){m1.df$severity_calc[i] = 6}
      else if (m1.df$SA_RRI_total_calc[i] <= 20){m1.df$severity_calc[i] = 7}
      else if (m1.df$SA_RRI_total_calc[i] <= 21){m1.df$severity_calc[i] = 8}
      else if (m1.df$SA_RRI_total_calc[i] <= 23){m1.df$severity_calc[i] = 9}
      else if (m1.df$SA_RRI_total_calc[i] >= 24){m1.df$severity_calc[i] = 10}
    }
  }
}


#### MODULE 2 AGGREGATION ####
AC.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/ADOS_Module_2.csv"
AC.df = df = read.csv(AC.file)
head(AC.df)

AC.df = AC.df[ which( ! AC.df$Subject.Id %in% c(NA, 'N/A', '')) , ]

AGRE.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADOS Mod2/ADOS21.csv"
AGRE.df = df = read.csv(AGRE.file)
head(AGRE.df)

svip1.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/ados_2.csv'
svip1.1 = df = read.csv(svip1.file)
svip1.1 = subset(svip1.1, ados_2.total >= 0)

svip2.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/ados_2.csv'
svip2.1 = df = read.csv(svip2.file)
svip2.1 = subset(svip2.1, ados_2.total >= 0)

SVIP.df = rbind(svip1.1, svip2.1)

SVIP2.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/svip_summary_variables.csv"
SVIP2.df = df = read.csv(SVIP2.file)
SVIP.gender = SVIP2.df[c('individual', 'svip_summary_variables.sex')]

SVIP.df = merge(SVIP.df, SVIP.gender, by = 'individual')

SSC.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ados_2_raw.csv"
SSC.df = df = read.csv(SSC.raw.file)
head(SSC.df)


SSC.twin.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_2_raw.csv"
SSC.twin.df = df = read.csv(SSC.twin.raw.file)
head(SSC.twin.df)


SSC.df = rbind(SSC.df, SSC.twin.df)

SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv"
SSC2.df = df = read.csv(SSC.file)
SSC.age = SSC2.df[c('individual', 'age_at_ados', 'sex')]

SSC.df = merge(SSC.df, SSC.age)



AGP2.file = "/scratch/PI/dpwall/DATA/phenotypes/AGP_pheno_all_201112/ados_mod_2wps.csv"
AGP.df = df = read.csv(AGP2.file)
AGP.df$Subject.Id = paste(AGP.df$FID, AGP.df$IID, sep = "-")


items = c('A1','A2','A3','A4','A5','A6','A7','A8','B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11','C1','C2','D1','D2','D3','D4','E1','E2','E3')
length(items)
colnames(AC.df)[12:33] = items[1:22]; colnames(AC.df)[35] = "D2"; colnames(AC.df)[37:38] = c("D3", "D4"); colnames(AC.df)[43:45] = c("E1" ,"E2", "E3")
colnames(SVIP.df)[7:34] = items
colnames(SSC.df)[3:30] = items
colnames(AGRE.df)[c(21,52,22:35,38:49)] = items
colnames(AGP.df)[5:32] = items


colnames(SVIP.df)[c(1,6)] = c('Subject.Id', 'age_months'); SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'male'] = 'M'; SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'female'] = 'F'
colnames(SSC.df)[c(1,31)] = c('Subject.Id', 'age_months'); SSC.df$gender[SSC.df$sex == 'male'] = 'M'; SSC.df$gender[SSC.df$sex == 'female'] = 'F'
colnames(AGRE.df)[7] = 'Subject.Id'; AGRE.df$age_months = AGRE.df$age*12; AGRE.df$gender[AGRE.df$Gender == 1] = 'M'; AGRE.df$gender[AGRE.df$Gender == 2] = 'F'; AGRE.df$gender = as.factor(AGRE.df$gender)
colnames(AC.df)[c(1,9,2)] = c('Subject.Id', 'age_months', 'gender')
colnames(AGP.df)[4] = 'age_months'; AGP.df$gender = NA

for(i in 5:32) {
  AGP.df[,i] <- as.numeric(AGP.df[,i])
}


myvars <- c('Subject.Id',items, 'age_months', 'gender')
AC.subset <- AC.df[myvars]
SVIP.subset <- SVIP.df[myvars]
AGRE.subset <- AGRE.df[myvars]
SSC.subset <- SSC.df[myvars]
AGP.subset <- AGP.df[myvars]

m2.df = rbind(AC.subset, SVIP.subset, AGRE.subset, SSC.subset)

#m2.df[,2:29][m2.df[,2:29] == '-1'] = 8
#m2.df[,2:29][m2.df[,2:29] < 0] = 8
#m2.df[,2:29][m2.df[,2:29] > 8] = 8

colnames(m2.df)
m2.recode = m2.df

m2.recode[,2:29][m2.recode[,2:29] < 0] = 8
m2.recode[,2:29][m2.recode[,2:29] >= 8] = 0
m2.recode[,2:29][m2.recode[,2:29] == 3] = 2

### When calculating sub- and total-scores, note that ALL databases have used ADOS-G numbering, so the algorithm changes as follows:
### ADOS-2 | ADOS-G
###   A4   |   A5
###   A6   |   A7
###   A7   |   A8
###   B11  |   B10
###   B12  |   B11


for (i in (1:length(m2.df$Subject.Id))){
  m2.df$social_affect_calc[i] = (m2.recode$A7[i] + m2.recode$A8[i] + m2.recode$B1[i] + m2.recode$B2[i] + m2.recode$B3[i] + m2.recode$B5[i] +
                                   m2.recode$B6[i] + m2.recode$B8[i] + m2.recode$B10[i] + m2.recode$B11[i])
  m2.df$restricted_repetitive_calc[i] = (m2.recode$A5[i] + m2.recode$D1[i] + m2.recode$D2[i] + m2.recode$D4[i])
  m2.df$SA_RRI_total_calc[i] = (m2.df$social_affect_calc[i] + m2.df$restricted_repetitive_calc[i])
}
for (i in (1:length(m2.df$social_affect_calc))){
  if (m2.df$age_months[i] < 36.0){
    if (m2.df$SA_RRI_total_calc[i] <= 2){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 6){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 8){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 9){m2.df$severity_calc[i] = 5}
    else if (m2.df$SA_RRI_total_calc[i] <= 11){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 12){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 14){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 17){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 18){m2.df$severity_calc[i] = 10}
  }
  else if (m2.df$age_months[i] < 48.0){
    if (m2.df$SA_RRI_total_calc[i] <= 3){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 6){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 8){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 9){m2.df$severity_calc[i] = 5}
    else if (m2.df$SA_RRI_total_calc[i] <= 12){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 14){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 16){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 18){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 19){m2.df$severity_calc[i] = 10}
  }
  else if (m2.df$age_months[i] < 60.0){
    if (m2.df$SA_RRI_total_calc[i] <= 3){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 6){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 7){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 9){m2.df$severity_calc[i] = 5}
    else if (m2.df$SA_RRI_total_calc[i] <= 13){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 16){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 18){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 20){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 21){m2.df$severity_calc[i] = 10}
  }
  else if (m2.df$age_months[i] < 84.0){
    if (m2.df$SA_RRI_total_calc[i] <= 3){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 7){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 8){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 14){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 16){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 20){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 22){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 23){m2.df$severity_calc[i] = 10}
  }
  else if (m2.df$age_months[i] < 108.0){
    if (m2.df$SA_RRI_total_calc[i] <= 2){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 7){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 8){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 14){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 17){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 21){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 23){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 24){m2.df$severity_calc[i] = 10}
  }
  else if (m2.df$age_months[i] >= 108.0){
    if (m2.df$SA_RRI_total_calc[i] <= 2){m2.df$severity_calc[i] = 1}
    else if (m2.df$SA_RRI_total_calc[i] <= 5){m2.df$severity_calc[i] = 2}
    else if (m2.df$SA_RRI_total_calc[i] <= 7){m2.df$severity_calc[i] = 3}
    else if (m2.df$SA_RRI_total_calc[i] <= 8){m2.df$severity_calc[i] = 4}
    else if (m2.df$SA_RRI_total_calc[i] <= 14){m2.df$severity_calc[i] = 6}
    else if (m2.df$SA_RRI_total_calc[i] <= 17){m2.df$severity_calc[i] = 7}
    else if (m2.df$SA_RRI_total_calc[i] <= 20){m2.df$severity_calc[i] = 8}
    else if (m2.df$SA_RRI_total_calc[i] <= 23){m2.df$severity_calc[i] = 9}
    else if (m2.df$SA_RRI_total_calc[i] >= 24){m2.df$severity_calc[i] = 10}
  } 
}

write.csv(m2.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m2_dirty.csv")




#### MODULE 3 AGGREGATION ####
AC.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/ADOS_Module_3.csv"
AC.df = df = read.csv(AC.file)
head(AC.df)

AC.df = AC.df[ which( ! AC.df$Subject.Id %in% c(NA, 'N/A', '')) , ]

AGRE.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADOS Mod3/ADOS31.csv"
AGRE.df = df = read.csv(AGRE.file)
head(AGRE.df)

svip1.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/ados_3.csv'
svip1.1 = df = read.csv(svip1.file)
svip1.1 = subset(svip1.1, ados_3.total >= 0)

svip2.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/ados_3.csv'
svip2.1 = df = read.csv(svip2.file)
svip2.1 = subset(svip2.1, ados_3.total >= 0)

SVIP.df = rbind(svip1.1, svip2.1)

SVIP2.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/svip_summary_variables.csv"
SVIP2.df = df = read.csv(SVIP2.file)
SVIP.gender = SVIP2.df[c('individual', 'svip_summary_variables.sex')]

SVIP.df = merge(SVIP.df, SVIP.gender, by = 'individual')

SSC.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ados_3_raw.csv"
SSC.df = df = read.csv(SSC.raw.file)
head(SSC.df)


SSC.twin.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_3_raw.csv"
SSC.twin.df = df = read.csv(SSC.twin.raw.file)
head(SSC.twin.df)


SSC.df = rbind(SSC.df, SSC.twin.df)

SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv"
SSC2.df = df = read.csv(SSC.file)
SSC.age = SSC2.df[c('individual', 'age_at_ados', 'sex')]

SSC.df = merge(SSC.df, SSC.age)


items = c('A1','A2','A3','A4','A5','A6','A7','A8','A9','B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','C1','D1','D2','D3','D4','D5','E1','E2','E3')
length(items)
colnames(AC.df)[12:32] = items [1:21]; colnames(AC.df)[34] = "D2"; colnames(AC.df)[35:37] = c("D3", "D4", "D5"); colnames(AC.df)[40:42] = items[26:28]
colnames(SVIP.df)[7:34] = items
colnames(SSC.df)[3:30] = items
colnames(AGRE.df)[c(21:36,38:49)] = items


colnames(SVIP.df)[c(1,6)] = c('Subject.Id', 'age_months'); SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'male'] = 'M'; SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'female'] = 'F'
colnames(SSC.df)[c(1,31)] = c('Subject.Id', 'age_months'); SSC.df$gender[SSC.df$sex == 'male'] = 'M'; SSC.df$gender[SSC.df$sex == 'female'] = 'F'
colnames(AGRE.df)[7] = 'Subject.Id'; AGRE.df$age_months = AGRE.df$age*12; AGRE.df$gender[AGRE.df$Gender == 1] = 'M'; AGRE.df$gender[AGRE.df$Gender == 2] = 'F'; AGRE.df$gender = as.factor(AGRE.df$gender)
colnames(AC.df)[c(1,9,2)] = c('Subject.Id', 'age_months', 'gender')


myvars <- c('Subject.Id',items, 'age_months', 'gender')
AC.subset <- AC.df[myvars]
SVIP.subset <- SVIP.df[myvars]
AGRE.subset <- AGRE.df[myvars]
SSC.subset <- SSC.df[myvars]


m3.df = rbind(AC.subset, SVIP.subset, AGRE.subset, SSC.subset)

#m3.df[,2:29][m3.df[,2:29] == '-1'] = 8
#m3.df[,2:29][m3.df[,2:29] < 0] = 8
#m3.df[,2:29][m3.df[,2:29] > 8] = 8

m3.recode = m3.df

m3.recode[,2:29][m3.recode[,2:29] < 0] = 8
m3.recode[,2:29][m3.recode[,2:29] >= 8] = 0
m3.recode[,2:29][m3.recode[,2:29] == 3] = 2


for (i in (1:length(m3.df$Subject.Id))){
  m3.df$social_affect_calc[i] = (m3.recode$A7[i] + m3.recode$A8[i] + m3.recode$A9[i] + m3.recode$B1[i] + m3.recode$B2[i] + m3.recode$B4[i] + m3.recode$B7[i] +
                                   m3.recode$B8[i] + m3.recode$B9[i] + m3.recode$B10[i])
  m3.df$restricted_repetitive_calc[i] = (m3.recode$A4[i] + m3.recode$D1[i] + m3.recode$D2[i] + m3.recode$D4[i])
  m3.df$SA_RRI_total_calc[i] = (m3.df$social_affect_calc[i] + m3.df$restricted_repetitive_calc[i])
}
for (i in (1:length(m3.df$social_affect_calc))){
  if (m3.df$age_months[i] < 72.0){
    if (m3.df$SA_RRI_total_calc[i] <= 3){m3.df$severity_calc[i] = 1}
    else if (m3.df$SA_RRI_total_calc[i] <= 4){m3.df$severity_calc[i] = 2}
    else if (m3.df$SA_RRI_total_calc[i] <= 6){m3.df$severity_calc[i] = 3}
    else if (m3.df$SA_RRI_total_calc[i] <= 7){m3.df$severity_calc[i] = 4}
    else if (m3.df$SA_RRI_total_calc[i] <= 8){m3.df$severity_calc[i] = 5}
    else if (m3.df$SA_RRI_total_calc[i] <= 11){m3.df$severity_calc[i] = 6}
    else if (m3.df$SA_RRI_total_calc[i] <= 12){m3.df$severity_calc[i] = 7}
    else if (m3.df$SA_RRI_total_calc[i] <= 15){m3.df$severity_calc[i] = 8}
    else if (m3.df$SA_RRI_total_calc[i] <= 17){m3.df$severity_calc[i] = 9}
    else if (m3.df$SA_RRI_total_calc[i] >= 18){m3.df$severity_calc[i] = 10}
  }
  else if (m3.df$age_months[i] < 120.0){
    if (m3.df$SA_RRI_total_calc[i] <= 2){m3.df$severity_calc[i] = 1}
    else if (m3.df$SA_RRI_total_calc[i] <= 4){m3.df$severity_calc[i] = 2}
    else if (m3.df$SA_RRI_total_calc[i] <= 6){m3.df$severity_calc[i] = 3}
    else if (m3.df$SA_RRI_total_calc[i] <= 7){m3.df$severity_calc[i] = 4}
    else if (m3.df$SA_RRI_total_calc[i] <= 8){m3.df$severity_calc[i] = 5}
    else if (m3.df$SA_RRI_total_calc[i] <= 10){m3.df$severity_calc[i] = 6}
    else if (m3.df$SA_RRI_total_calc[i] <= 12){m3.df$severity_calc[i] = 7}
    else if (m3.df$SA_RRI_total_calc[i] <= 14){m3.df$severity_calc[i] = 8}
    else if (m3.df$SA_RRI_total_calc[i] <= 17){m3.df$severity_calc[i] = 9}
    else if (m3.df$SA_RRI_total_calc[i] >= 18){m3.df$severity_calc[i] = 10}
  }
  else if (m3.df$age_months[i] >= 120.0){
    if (m3.df$SA_RRI_total_calc[i] <= 3){m3.df$severity_calc[i] = 1}
    else if (m3.df$SA_RRI_total_calc[i] <= 4){m3.df$severity_calc[i] = 2}
    else if (m3.df$SA_RRI_total_calc[i] <= 6){m3.df$severity_calc[i] = 3}
    else if (m3.df$SA_RRI_total_calc[i] <= 7){m3.df$severity_calc[i] = 4}
    else if (m3.df$SA_RRI_total_calc[i] <= 8){m3.df$severity_calc[i] = 5}
    else if (m3.df$SA_RRI_total_calc[i] <= 10){m3.df$severity_calc[i] = 6}
    else if (m3.df$SA_RRI_total_calc[i] <= 12){m3.df$severity_calc[i] = 7}
    else if (m3.df$SA_RRI_total_calc[i] <= 14){m3.df$severity_calc[i] = 8}
    else if (m3.df$SA_RRI_total_calc[i] <= 17){m3.df$severity_calc[i] = 9}
    else if (m3.df$SA_RRI_total_calc[i] >= 18){m3.df$severity_calc[i] = 10}
  }
}

write.csv(m3.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m3_dirty.csv")

#### MODULE 4 AGGREGATION #### 
AC.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/ADOS_Module_4.csv"
AC.df = df = read.csv(AC.file)
colnames(AC.df)

AC.df = AC.df[ which( ! AC.df$Subject.Id %in% c(NA, 'N/A', '')) , ]

AGRE.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADOS Mod4/ADOS41.csv"
AGRE.df = df = read.csv(AGRE.file)
colnames(AGRE.df)

svip1.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/ados_4.csv'
svip1.1 = df = read.csv(svip1.file)
svip1.1 = subset(svip1.1, ados_4.stereotyped_behaviors >= 0)

svip2.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/ados_4.csv'
svip2.1 = df = read.csv(svip2.file)
svip2.1 = subset(svip2.1, ados_4.stereotyped_behaviors >= 0)

SVIP.df = rbind(svip1.1, svip2.1)

SVIP2.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/svip_summary_variables.csv"
SVIP2.df = df = read.csv(SVIP2.file)
SVIP.gender = SVIP2.df[c('individual', 'svip_summary_variables.sex')]

SVIP.df = merge(SVIP.df, SVIP.gender, by = 'individual')

SSC.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ados_4_raw.csv"
SSC.df = df = read.csv(SSC.raw.file)
head(SSC.df)


SSC.twin.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_4_raw.csv"
SSC.twin.df = df = read.csv(SSC.twin.raw.file)
head(SSC.twin.df)

SSC.df = rbind(SSC.df, SSC.twin.df)

SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv"
SSC2.df = df = read.csv(SSC.file)
SSC.age = SSC2.df[c('individual', 'age_at_ados', 'sex')]

SSC.df = merge(SSC.df, SSC.age)


items = c('A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11',"B12",'C1','D1','D2','D3','D4','D5','E1','E2','E3')
length(items)
colnames(AC.df)[12:35] = items [1:24]; colnames(AC.df)[37] = "D2"; colnames(AC.df)[39:41] = c("D3", "D4", "D5"); colnames(AC.df)[43:45] = items[29:31]
colnames(SVIP.df)[7] = items[1]; colnames(SVIP.df)[8] = items[10]; colnames(SVIP.df)[9:16] = items[2:9]; colnames(SVIP.df)[17:37] = items[11:31]
colnames(SSC.df)[3] = items[10]; colnames(SSC.df)[4:33] = items[c(1:9,11:31)]
colnames(AGRE.df)[c(21:39,41:52)] = items

colnames(SVIP.df)[c(1,6)] = c('Subject.Id', 'age_months'); SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'male'] = 'M'; SVIP.df$gender[SVIP.df$svip_summary_variables.sex == 'female'] = 'F'
colnames(SSC.df)[c(1,34)] = c('Subject.Id', 'age_months'); SSC.df$gender[SSC.df$sex == 'male'] = 'M'; SSC.df$gender[SSC.df$sex == 'female'] = 'F'
colnames(AGRE.df)[7] = 'Subject.Id'; AGRE.df$age_months = AGRE.df$age*12; AGRE.df$gender[AGRE.df$Gender == 1] = 'M'; AGRE.df$gender[AGRE.df$Gender == 2] = 'F'; AGRE.df$gender = as.factor(AGRE.df$gender)
colnames(AC.df)[c(1,9,2)] = c('Subject.Id', 'age_months', 'gender')


myvars <- c('Subject.Id',items, 'age_months', 'gender')
AC.subset <- AC.df[myvars]
SVIP.subset <- SVIP.df[myvars]
AGRE.subset <- AGRE.df[myvars]
SSC.subset <- SSC.df[myvars]

m4.df = rbind(AC.subset, SVIP.subset, AGRE.subset, SSC.subset)

m4.df[,2:32][m4.df[,2:32] == '-1'] = 8
m4.df[,2:32][m4.df[,2:32] < 0] = 8
m4.df[,2:32][m4.df[,2:32] > 8] = 8

m4.recode = m4.df

m4.recode[,2:32][m4.recode[,2:32] < 0] = 8
m4.recode[,2:32][m4.recode[,2:32] >= 8] = 0
m4.recode[,2:32][m4.recode[,2:32] == 3] = 2


for (i in (1:length(m4.df$Subject.Id))){
  m4.df$communication_calc[i] = (m4.recode$A4[i] + m4.recode$A8[i] + m4.recode$A9[i] + m4.recode$A10[i])
  m4.df$social_interaction_calc[i] = (m4.recode$B1[i] + m4.recode$B2[i] + m4.recode$B6[i] + m4.recode$B8[i] + 
                                        m4.recode$B9[i] + m4.recode$B11[i] + m4.recode$B12[i])
  m4.df$communication_social_total_calc[i] = (m4.df$communication_calc[i] + m4.df$social_interaction_calc[i])
}

colnames(m1.df)[2:30] <- paste("ados_M1", colnames(m1.df)[2:30], sep = "_")
colnames(m2.df)[2:29] <- paste("ados_M2", colnames(m2.df)[2:29], sep = "_")
colnames(m3.df)[2:29] <- paste("ados_M3", colnames(m3.df)[2:29], sep = "_")
colnames(m4.df)[2:32] <- paste("ados_M4", colnames(m4.df)[2:32], sep = "_")

########################################################################################
######################################### ADIR #########################################
########################################################################################

#Read in AC file
AC.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/ADI_R.csv"
AC.df = df = read.csv(AC.file)
colnames(AC.df)

AC.df = AC.df[ which( ! AC.df$Subject.Id %in% c(NA, 'N/A', '')) , ]

# Read in AGRE files and aggregate
AGRE1.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADIR/ADIR1.csv"
AGRE1.df = df = read.csv(AGRE1.file)

AGRE2.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/ADIR/ADIR2.csv"
AGRE2.df = df = read.csv(AGRE2.file)

AGRE.df = merge(AGRE1.df, AGRE2.df, by = "Individual.ID", all = T)


# Read in SVIP files and aggregate
SVIP.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/adi_r.csv"
SVIP1.df = df = read.csv(SVIP.file)
SVIP1.df = subset(SVIP1.df, adi_r.measure.eval_age_months >= 0)

SVIP.file = "/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/adi_r.csv"
SVIP2.df = df = read.csv(SVIP.file)
SVIP2.df = subset(SVIP2.df, adi_r.measure.eval_age_months >= 0)

SVIP.df = rbind(SVIP1.df, SVIP2.df)

colnames(SVIP.df)

## Read in SSC files and aggregate
SSC.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/adi_r.csv"
SSC.df = df = read.csv(SSC.raw.file)

SSCtwin.raw.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/adi_r.csv"
SSCtwin.df = df = read.csv(SSCtwin.raw.file)

SSC.df = rbind(SSC.df, SSCtwin.df)

## create vector for proper column names
items = c('q01_current_concens', colnames(SSC.df)[3], 'q03_first_symptoms', colnames(SSC.df)[c(5,6,8,10,12,14,16,18:24,26,27,29:35,37,39:154,156:167)])

SSC.df$q01_current_concens = NA; SSC.df$q03_first_symptoms = NA; SVIP.df$q01_current_concens = NA; SVIP.df$q03_first_symptoms = NA;

colnames(SVIP.df)[c(193,28,194,30,31,33,35,37,39,41,43:49,51,52,54:60,62,64:179,181:192)] = items
colnames(AGRE.df)[c(23,25:26,28:29,31:33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63,65,67,69,71,73,76,75,77:79,81,80,82:89,91:92,94:95,97:98,100:101,104,103,107,106,109,108,112,111,115,114,117,116,120,119,123,122,125,124,127,126,129,128,131,130,133,132,135,134,137,136,139,138,141,140,143:144,147,146,150,149,152,151,154,153,156,155,158,157,160,159,162,161,163:188,190,189,191:214)] = items
colnames(AC.df)[c(36,37,39:41,43,45,47,49,51,53:59,61,63,65:71,73,75,78,77,79:81,83,82,84:99,101,100,103,102,105,104,107,106,109,108,111,110,113,112,115,114,117,116,119,118,121,120,123,122,125,124,127,126,129,128,131,130,133,132,135:136,138,137,142,141,144,143,146,145,148,147,150,149,152,151,154,153,155:180,182,181,183:206)]= items

colnames(AGRE.df)[1] = 'Subject.Id'
colnames(SSC.df)[1] = 'Subject.Id'
colnames(SVIP.df)[1] = 'Subject.Id'

myvars <- c('Subject.Id',items)
AC.subset <- AC.df[myvars]
SVIP.subset <- SVIP.df[myvars]
AGRE.subset <- AGRE.df[myvars]
SSC.subset <- SSC.df[myvars]

adir.df = rbind(AC.subset, SVIP.subset, AGRE.subset, SSC.subset)

adir.df[,2:156][adir.df[,2:156] == '-1'] = 8
adir.df[,2:156][adir.df[,2:156] < 0] = 8
adir.df[,2:156][adir.df[,2:156] >= 900] = 8

colnames(adir.df)[2:156] <- paste("adir", colnames(adir.df)[2:156], sep = "_")

########################################################################################
######################################### SRS  #########################################
########################################################################################


### Unaffected Sibling ###
unaffSib = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/srs_parent_raw.csv"
unaffSibSRS = df = read.csv(unaffSib)
unaffSibSRS = unaffSibSRS[,c(1,3:67)]
sibAge.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/sibling_DOB2.csv"
sibAge.df = df = read.csv(sibAge.file)
sibAge.df = sibAge.df[c('Sibling_ID',"Sibling_age_months", "Sibling_Sex")]
colnames(sibAge.df) = c('individual', 'age_at_ados', 'sex')
sibsSRS = merge(unaffSibSRS, sibAge.df, all.x=T)
sibsSRS$gender[sibsSRS$sex == 'male'] = 'M'; sibsSRS$gender[sibsSRS$sex == 'female'] = 'F'

### Proband ###
proband = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/srs_parent_raw.csv"
probandSRS = df = read.csv(proband)

### MZ Twin ###
twin = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/srs_parent_raw.csv"
twinSRS = df = read.csv(twin)

sscSRS = rbind(probandSRS, twinSRS)

sscSRS = sscSRS[,c(1,3:67)]

SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv"
SSC1.df = df = read.csv(SSC.file)
SSC.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ssc_core_descriptive.csv"
SSC2.df = df = read.csv(SSC.file)
SSC.age = rbind(SSC1.df, SSC2.df)
SSC.age = SSC.age[c('individual', 'age_at_ados', 'sex')]

sscSRS = merge(sscSRS, SSC.age, all.x=T)
sscSRS$gender[sscSRS$sex == 'male'] = 'M'; sscSRS$gender[sscSRS$sex == 'female'] = 'F'
sscSRS = rbind(sscSRS, sibsSRS)
sscSRS = sscSRS[,c(1,67,69,2:66)]
colnames(sscSRS)[2] = 'age_months'
## AC ##
ac = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/SRS_Parent.csv"
acSRS = df = read.csv(ac)
acSRS = acSRS[,c(1,9,2,12:76)]

## AGRE ##
agre = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/SRS/SRS2_SRS20021.csv"
agreSRS = df = read.csv(agre)
agreSRS = agreSRS[,c(7,17,6,25:89)]
agreSRS$age_months = agreSRS$age*12; agreSRS$gender[agreSRS$Gender == 1] = 'M'; agreSRS$gender[agreSRS$Gender == 2] = 'F'; agreSRS$gender = as.factor(agreSRS$gender)
agreSRS = agreSRS[,c(1,69:70,4:68)]

colnames(acSRS) = colnames(sscSRS)
colnames(agreSRS) = colnames(sscSRS)
srs.df = rbind(sscSRS, acSRS, agreSRS)
colnames(srs.df)[1] = 'Subject.Id'
colnames(srs.df)[2:66] <- paste("srs", colnames(srs.df)[2:66], sep = "_")

########################################################################################
######################################### SCQ  #########################################
########################################################################################

## SSC ##
unaffSib = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/scq_life_raw.csv"
unaffSibSCQ = df = read.csv(unaffSib)

proband = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/scq_life_raw.csv"
probandSCQ = df = read.csv(proband)

twin = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/scq_life_raw.csv"
twinSCQ = df = read.csv(twin)

sscSCQ = rbind(unaffSibSCQ, probandSCQ, twinSCQ)
sscSCQ = sscSCQ[,c(1,3:42)]


## AC ##
ac = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/SCQ_Lifetime.csv"
acSCQ = df = read.csv(ac)
acSCQ = acSCQ[,c(1,12:51)]
acSCQ[,2:41][acSCQ[,2:41] >= 900] = NA

convert.magic <- function(obj, type){
  FUN1 <- switch(type,
                 character = as.character,
                 numeric = as.numeric,
                 factor = as.factor)
  out <- lapply(obj, FUN1)
  as.data.frame(out)
}

acSCQ = convert.magic(acSCQ, "factor")


## AGRE ##
agre = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/SCQ/SCQ_20031.csv"
agreSCQ = df = read.csv(agre)
agreSCQ = agreSCQ[,c(7,21:60)]
agreSCQ[,2:41][agreSCQ[,2:41] >= 900] = NA
agreSCQ[,2:41][agreSCQ[,2:41] < 0] = NA

agreSCQ = convert.magic(agreSCQ, "factor")

colnames(acSCQ) = colnames(sscSCQ)
colnames(agreSCQ) = colnames(sscSCQ)
SCQ.df = rbind(sscSCQ, acSCQ, agreSCQ)
colnames(SCQ.df)[1] = 'Subject.Id'
colnames(SCQ.df)[2:41] <- paste("scq", colnames(SCQ.df)[2:41], sep = "_")

########################################################################################
######################################## RBS-R #########################################
########################################################################################

## SSC ##
proband = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/rbs_r_raw.csv"
probandRBS = df = read.csv(proband)

twin = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/rbs_r_raw.csv"
twinRBS = df = read.csv(twin)

sscRBS = rbind(probandRBS, twinRBS)
sscRBS = sscRBS[,c(1,3:45)]

## AC ##
ac = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/RBS_R.csv"
acRBS = df = read.csv(ac)
acRBS = acRBS[,c(1,12:54)]

colnames(acRBS) = colnames(sscRBS)
RBS.df = rbind(sscRBS, acRBS)
colnames(RBS.df)[1] = "Subject.Id"
colnames(RBS.df)[2:44] <- paste("rbs", colnames(RBS.df)[2:44], sep = "_")

########################################################################################
###################################### DIAGNOSES #######################################
########################################################################################


### AGRE ###
agre.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/AGRE Pedigree Catalog 10-05-12/AGRE Pedigree Catalog 10-05-2012.csv"
agre1.df = df = read.csv(agre.file)
agre1.df = agre1.df[,c(3,12)]
colnames(agre1.df) = c("Subject.Id", "Diagnosis")
agre1.df$ASD[agre1.df[,2] %in% c("Autism", "ASD", "PDD-NOS", "BroadSpectrum")] = 1
agre1.df$ASD[agre1.df[,2] %in% c('Not Met', "NQA")] = 0
agre.diag = agre1.df
agre.asd = agre1.df[,c(1,3)]

agre3.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/Medical History Affected Child/AffChild3.csv"
agre2.df = df = read.csv(agre3.file)
agre2.df = agre2.df[,c(4,18)]
colnames(agre2.df) = c('individual', 'ADHD')
agre2.df$ADHD[agre2.df$ADHD %in% c(-1, 9)] = 0

agre.file = "/scratch/PI/dpwall/DATA/phenotypes/AGRE_2015/Medical History Unaffected Child/Unaffec1.csv"
agre3.df = df = read.csv(agre.file)
agre3.df = agre3.df[,c(7,112)]
colnames(agre3.df) = c('individual', 'ADHD')
agre3.df$ADHD[agre3.df$ADHD %in% c(-1, 9)] = 0

agre.adhd = rbind(agre2.df, agre3.df)

agre.df = merge(agre.asd, agre.adhd, all=T)

### AC ###
ac.file = "/scratch/PI/dpwall/DATA/phenotypes/Autism_Consortium_Data/All_Measures/AC_Medical_History.csv"
ac.df = df = read.csv(ac.file)
colnames(ac.df)[1] = 'Subject.Id'
#ac.df$ADHD = 0
#ac.df$ADHD[ac.df$ACCMHF_ADD %in% c(1,2,3,4)] = 1
ac.df$ASD = 0
ac.df$ASD[ac.df$ACCMHF_ASDChild %in% c(1,2)] = 1
ac.df$Diagnosis = "None"
ac.df$Diagnosis[ac.df$ACCMHF_ASDChild == 1] = 'autism'
ac.df$Diagnosis[ac.df$ACCMHF_ASDChild == 2] = 'autism spectrum'
ac.diag = ac.df[,c(1,1403,1402)]

### SSC ###
ssc1.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_diagnosis.csv"
ssc2.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ssc_diagnosis.csv"
ssc6.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Proband Data/medhx_fam_psychiatric1.csv"
ssc1.df = df = read.csv(ssc1.file)
ssc2.df = df = read.csv(ssc2.file)
ssc3.df = rbind(ssc1.df, ssc2.df)
ssc6.df = df = read.csv(ssc6.file)

ssc.df = merge(ssc3.df, ssc6.df, by='individual')
ssc.df$Diagnosis = ssc.df$q1a_autism_spectrum_dx
ssc.df$ASD = 0
ssc.df$ASD[ssc.df$q1_autism_spectrum == 'yes'] = 1
#ssc.df$ADHD = 0
#ssc.df$ADHD[ssc.df$attention_deficit_proband == 'true'] = 1
ssc.diag = ssc.df[,c(1,146:147)]
colnames(ssc.diag)[1] = "Subject.Id"


sibs1.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/adhd.csv"
sibs2.file = "/scratch/PI/dpwall/DATA/phenotypes/SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/ssc_summary_variables.csv"

sibs1.df = df = read.csv(sibs1.file)
sibs2.df = df = read.csv(sibs2.file)
sib.df = merge(sibs2.df, sibs1.df, by='individual', all=T)
sib.df$ASD = 0
sib.df$ADHD2 = 0
sib.df$ADHD2[sib.df$ADHD == '1'] = 1
sib.df = sib.df[,c(1,4,5)]
colnames(sib.df)[3] = 'ADHD'

ssc.df = rbind(ssc.df, sib.df)

### SVIP ###
svip1.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_1q21.1/diagnosis_summary.csv'
svip1.df = df = read.csv(svip1.file)
svip1.df = svip1.df[,c(1,7,14,70)]
svip2.file = '/scratch/PI/dpwall/DATA/phenotypes/SVIP/SVIP_16p11.2/diagnosis_summary.csv'
svip2.df = df = read.csv(svip2.file)
svip2.df = svip2.df[,c(1,7,14,70)]
svip.df = rbind(svip1.df, svip2.df)
colnames(svip.df)
svip.df$Diagnosis = svip.df$diagnosis_summary.diagnosis_summary.v1a_diagnosis
svip.df$ASD = 0
svip.df$ASD[svip.df$diagnosis_summary.clinical_asd_dx == 'true'] = 1
#svip.df$ADHD = 0
#svip.df$ADHD[svip.df$diagnosis_summary.adhd_diagnosis == 'true'] = 1
#svip.df = svip.df[,c(1,4:5)]
svip.diag = svip.df[,c(1,5,6)]
colnames(svip.diag)[1] = "Subject.Id"

all.diags = rbind(ac.diag, agre.diag, ssc.diag, svip.diag)
diagnoses.df = rbind(ac.df, agre.df, ssc.df, svip.df)
colnames(diagnoses.df)[1] = "Subject.Id"
########################################################################################
######################################## ALL.df ########################################
########################################################################################

m1.df = merge(m1.df, all.diags, all.x=T)
m2.df = merge(m2.df, all.diags, all.x=T)
m3.df = merge(m3.df, all.diags, all.x=T)
m4.df = merge(m4.df, all.diags, all.x=T)
adir.df = merge(adir.df, all.diags, all.x=T)

write.csv(m1.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m1.csv")
write.csv(m2.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m2.csv")
write.csv(m3.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m3.csv")
write.csv(m4.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADOS_m4.csv")
write.csv(adir.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/ADIR.csv")

all.df = merge(m1.df, m2.df, all=T)
all.df = merge(all.df, m3.df, all = T)
all.df = merge(all.df, m4.df, all = T)
all.df = merge(all.df, adir.df, all = T)
all.df = merge(all.df, srs.df, all = T)
all.df = merge(all.df, SCQ.df, all= T)
all.df = merge(all.df, RBS.df, all = T)
all.df = merge(all.df, diagnoses.df, all = T)

write.csv(all.df, "/scratch/PI/dpwall/DATA/phenotypes/aggregated_files/pheno_matrix.csv")