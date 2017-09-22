# We currently have four phenotype datasets:
# Autism Genetic Resource Exchange (AGRE)
# Autism Consortium (AC)
# National Database for Autism Research (NDAR)
# Simons Simplex Collection (SSC)

# We're working on getting access to one more:
# Autism Treatment Network (ATN)

# Each of these datasets has collected different phenotype information about its participants,
# but all five contain ADIR and ADOS so we're starting there.

# Raw data can be found on sherlock /scratch/PI/dpwall/DATA/phenotypes

# In writing this script, I added two files to the phenotypes directory on sherlock:
# secondary_diagnoses_categories.txt - manual curation of secondary diagnoses from AGRE into categories done by Chloe
# secondary_diagnoses - manual cleanup of secondary diagnoses from AGRE done by Preston

# This code requires a path to our phenotype data.
# It outputs a file called all_samples_stage1.json which contains aggregated phenotype data across our
# four datasets.
# It is meant to be run as part of a multi-stage pipeline described in the README.

# The code can be run with:
# python3 aggregate_phenotype.py path-to-phenotype-data



import json
import jsonschema
import csv
import os
import sys

# Load schema
with open("AutismPhenotype.json") as schema_file:    
	pheno_schema = json.load(schema_file)

# For each instrument, pull coded feature values from the schema
instrument_to_codes = {}
for instrument in pheno_schema['definitions']:
	instrument_to_codes[instrument] = {}
	for feature in pheno_schema['definitions'][instrument]['properties'].keys():
		if feature.startswith('Q') and not feature.endswith('a'):
			# If it has an 'a' counterpart, then it contains coded values
			if feature + 'a' in pheno_schema['definitions'][instrument]['properties']:
				coded_values = pheno_schema['definitions'][instrument]['properties'][feature + 'a']['enum'][:]
				coded_values.remove(None)
				coded_values.remove(0)
				instrument_to_codes[instrument][feature] = set(coded_values)
			else:
				instrument_to_codes[instrument][feature] = None

# These are entry errors in our datasets that need to be taken care of
instrument_to_exceptions = {
	"ADIR": {
		"Q05": {'994': None},
		"Q06": {'910': None},
		"Q07": {'966': None},
		"Q08": {'9999': None},
		"Q11": {'999': None, '9': None},
		"Q20": {'8':'0', '998':'0', '9': None},
		"Q21": {'8':'0', '998':'0', '9': None},
		"Q22": {'8':'0', '998':'0', '9': None},
		"Q23": {'8':'0', '998':'0', '9': None},
		"Q24": {'8':'0', '998':'0', '9': None},
		"Q25": {'8':'0', '998':'0', '9': None},
		"Q26": {'0': '998', '8':'998', '9': None, '990': None},
		"Q27": {'998':'8', '9': None},
		"Q28": {'8':'998', '9': None, '995': None, '990': None},
		"Q30": {'9': None},
		"Q38.1": {'3': '2'},
		"Q42.1": {'3': '2'},
		"Q42.2": {'3': '2'},
		"Q54.1": {'3': '2'},
		"Q54.2": {'3': '2'},
		"Q67.1": {'8': None},
		"Q67.2": {'8': None},
		"Q71.1": {'3': '2'},
		"Q71.2": {'3': '2'},
		"Q72.2": {'3': '2', '8': None},
		"Q74.2": {'8': None},
		"Q86": {'13': None, '18': None},
		"Q87": {'999': None, '998': None, '992': None, '995': None},
		"Q88.2": {'3': '2'},
		"Q90.1": {'3': '2'},
		"Q90.2": {'3': '2'},
		"Q91.2": {'4': None},
		"Q92.2": {'3': '2'}
	},
	"ADOS_Module1": {
		"QA01": {'8': '4'},
		"QB02": {'8': None},
		"QB07": {'8': None},
		"QB11": {'8': None},
		"QD03": {'3': '2', '8': None}
	},
	"ADOS_Module2": {
		"QA01": {'7': None},
		"QA04": {'8': None},
		"QA05": {'8': None},
		"QB03": {'8': None},
		"QD03": {'3': '2'}
	},
	"ADOS_Module3": {
		"QA02": {'8': None},
		"QB01": {'1': None},
		"QB04": {'8': None},
		"QB05": {'3': '2'},
		"QB06": {'8': None},
		"QB09": {'8': None},
		"QC01": {'8': None},
		"QD03": {'3': '2'},
		"QE03": {'3': '2'}
	},
	"ADOS_Module4": {
		"QB01": {'1': None},
		"QB06": {'3': '2'},
		"QB12": {'8': None},
		"QC01": {'8': None},
	}
}

# These are "missing data" values used in our datasets
instrument_to_missing_data = {
	"ADIR": {None, '', ' ', 'N/A', '-1', '900', '904'},
	"ADOS_Module1": {None, '', ' ', '-1', '995', '900', '9', '999'},
	"ADOS_Module2": {None, '', ' ', '-1', '900', '999', '9'},
	"ADOS_Module3": {None, '', ' ', '-1', '-5', '900', '9', '999'},
	"ADOS_Module4": {None, '', ' ', '-1', '9'}
}

# These samples have major data issues - for example doubled entries marked as two different genders
bad_samples = {('National Database for Autism Research', 'NDARXR035XHH'),
				('National Database for Autism Research', 'NDARTF820BMV')}

# These are aggregated features, scores, and diagnoses that will be filled in by assign_diagnosis.py
instrument_to_scores = {
	"ADIR": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior', 'abnormality_evident_before_3_years',
		'A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'],
	"ADOS_Module1": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS_Module2": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS_Module3": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS_Module4": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior']}

# Grab directory
directory = sys.argv[1]

# We'll fill up this dictionary with samples
identifier_to_samples = {}

# This is a very general method that converts csv data to json given a mapping
def convert_phenotypes(filename, dataset, instrument, lambdas, cols, num_headers=1, delimiter=','):
	print("Importing %s" % filename)

	with open("%s/%s" % (directory, filename), encoding='utf-8', errors='ignore') as f:
		reader = csv.reader(f, delimiter=delimiter)

		# Skip header
		for _ in range(num_headers):
			next(reader)

		for pieces in reader:
			# Pull sample information
			identifier = lambdas["identifier"](pieces)
			gender = lambdas["gender"](pieces)
			race = lambdas["race"](pieces)
			ethnicity = lambdas["ethnicity"](pieces)
			family = lambdas["family"](pieces)

			# Determine whether or not we've already seen this sample
			if (dataset, identifier) in identifier_to_samples:
				sample = identifier_to_samples[(dataset, identifier)]

				# Update sample with new information, if it exists
				if sample["gender"] is None:
					sample["gender"] = gender
				elif gender is not None and sample["gender"] != gender:
					print("Gender mismatch", dataset, identifier, sample["gender"], gender)

				if sample["race"] is None:
					sample["race"] = race
				elif race is not None and sample["race"] != race:
					print("Race mismatch", dataset, identifier, sample["race"], race)

				if sample["ethnicity"] is None:
					sample["ethnicity"] = ethnicity
				elif race is not None and sample["ethnicity"] != ethnicity:
					print("Ethnicity mismatch", dataset, identifier, sample["ethnicity"], ethnicity)

				if sample["family"] is None:
					sample["family"] = family
				elif race is not None and sample["family"] != family:
					print("Family mismatch", dataset, identifier, sample["family"], family)
			else:
				# Create new sample
				sample = {
					"dataset": dataset,
					"identifier": identifier,
					"gender": gender,
					"race": race,
					"ethnicity": ethnicity,
					"family": family,
					"diagnosis": None,
					"clinical_diagnosis": None,
					"cpea_diagnosis": None,
					"cpea_adjusted_diagnosis": None
				}
				identifier_to_samples[(dataset, identifier)] = sample

			# Skip bad samples
			if (dataset, identifier) not in bad_samples:

				# Only pull latest instrument for each sample
				age = lambdas["age"](pieces)
				if (instrument not in sample) or (sample[instrument]["age"] is None) or (age is not None and sample[instrument]["age"] < age):
					sample[instrument] = {
						"age": age,
						"interview_date": lambdas["interview_date"](pieces),
					}

					# Add empty scores for each instrument to be filled in later
					for score in instrument_to_scores[instrument]:
						sample[instrument][score] = None

					# Pull phenotype information
					exceptions = instrument_to_exceptions[instrument]
					codes = instrument_to_codes[instrument]
					missing_data = instrument_to_missing_data[instrument]

					for q_num, col in cols.items():
						# If answer is split into multiple columns, combine them
						if isinstance(col, tuple):
							answer = pieces[col[1]] if pieces[col[0]] in missing_data else pieces[col[0]]
							if len(col) != 2:
								print('Tuple longer than expected:', col)
						elif col == None:
							answer = None
						else:
							answer = pieces[col]

						# Transform answer in the case of an exception
						if q_num in exceptions:
							q_except = exceptions[q_num]
							if answer in q_except:
								answer = q_except[answer]

						# Grab set of code values from table
						coded_values = codes['default'] if q_num not in codes else codes[q_num]

						# Determine the ordinal and coded value for this entry
						ord_value = None
						cod_value = None

						if answer in missing_data:
							pass
						else:
							answer = int(round(float(answer), 0))
							if coded_values is not None:
								ord_value = answer if answer not in coded_values else None
								cod_value = answer if answer in coded_values else 0
							else:
								ord_value = answer
						
						# Enter values into sample
						sample[instrument][q_num] = ord_value
						if coded_values is not None:
							sample[instrument]["%sa" % q_num] = cod_value

					jsonschema.validate(sample, pheno_schema)

# ***************************************************************************************************************
# *
# --------------------------------------------------- AGRE ------------------------------------------------------
# *
# ***************************************************************************************************************

# 2015 ADIR
dataset = "AGRE"
instrument = "ADIR"
filename = "AGRE_2015/ADIR/ADIR1.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[16]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
		"family": lambda x: x[10]
	}, 
	{
		"Q02": 24, "Q04": 27, "Q05": 28, "Q06": 30, "Q07": 31, "Q08": 32, "Q09": 34, "Q10": 36,
		"Q11": 38, "Q12": 40, "Q13": 42, "Q14": 44, "Q15": 46, "Q16": 48, "Q17": 50, "Q18": 52, "Q19": 54, "Q20": 56,
		"Q21": 58, "Q22": 60, "Q23": 62, "Q24": 64, "Q25": 66, "Q26": 68, "Q27": 70, "Q28": 72, "Q29.1": 74, "Q29.2": 75, "Q30": 76,
		"Q31.1": 77, "Q31.2": 78, "Q32.1": 79, "Q32.2": 80, "Q33.1": 81, "Q33.2": 82, "Q34.1": 83, "Q34.2": 84, "Q35.1": 85, "Q35.2": 86, "Q36.1": 87, "Q36.2": 88, "Q37.1": 90, "Q37.2": 91, "Q38.1": 93, "Q38.2": 94, "Q39.1": 96, "Q39.2": 97, "Q40.1": 99, "Q40.2": 100,
		"Q41.1": 102, "Q41.2": 103, "Q42.1": 105, "Q42.2": 106, "Q43.1": 107, "Q43.2": 108, "Q44.1": 110, "Q44.2": 111, "Q45.1": 113, "Q45.2": 114, "Q46.1": 115, "Q46.2": 116, "Q47.1": 118, "Q47.2": 119, "Q48.1": 121, "Q48.2": 122, "Q49.1": 123, "Q49.2": 124, "Q50.1": 125, "Q50.2": 126,
		"Q51.1": 127, "Q51.2": 128, "Q52.1": 129, "Q52.2": 130, "Q53.1": 131, "Q53.2": 132, "Q54.1": 133, "Q54.2": 134, "Q55.1": 135, "Q55.2": 136, "Q56.1": 137, "Q56.2": 138, "Q57.1": 139, "Q57.2": 140, "Q58.1": 142, "Q58.2": 143, "Q59.1": 145, "Q59.2": 146, "Q60.1": 148, "Q60.2": 149,
		"Q61.1": 150, "Q61.2": 151, "Q62.1": 152, "Q62.2": 153, "Q63.1": 154, "Q63.2": 155, "Q64.1": 156, "Q64.2": 157, "Q65.1": 158, "Q65.2": 159, "Q66.1": 160, "Q66.2": 161, "Q67.1": 162, "Q67.2": 163, "Q68.1": 164, "Q68.2": 165, "Q69.1": 166, "Q69.2": 167, "Q70.1": 168, "Q70.2": 169,
		"Q71.1": 170, "Q71.2": 171, "Q72.1": 172, "Q72.2": 173, "Q73.1": 174, "Q73.2": 175, "Q74.1": 176, "Q74.2": 177, "Q75.1": 178, "Q75.2": 179, "Q76.1": 180, "Q76.2": 181, "Q77.1": 182, "Q77.2": 183, "Q78.1": 184, "Q78.2": 185, "Q79.1": 186, "Q79.2": 187, "Q80.1": 188, "Q80.2": 189,
		"Q81.1": 190, "Q81.2": 191, "Q82.1": 192, "Q82.2": 193, "Q83.1": 194, "Q83.2": 195, "Q84.1": 196, "Q84.2": 197, "Q85.1": 198, "Q85.2": 199, "Q86": 200, "Q87": 201, "Q88.1": 202, "Q88.2": 203, "Q89.1": 204, "Q89.2": 205, "Q90.1": 206, "Q90.2": 207,
		"Q91.1": 208, "Q91.2": 209, "Q92.1": 210, "Q92.2": 211, "Q93.1": 212, "Q93.2": 213
	})

# 2010 ADIR
filename = "AGRE_2010/ADIR/ADIR1.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
		"family": lambda x: x[7]
	}, 
	{
		"Q02": 20, "Q04": 23, "Q05": 24, "Q06": 26, "Q07": 27, "Q08": 28, "Q09": 30, "Q10": 32,
		"Q11": 34, "Q12": 36, "Q13": 38, "Q14": 40, "Q15": 42, "Q16": 44, "Q17": 46, "Q18": 48, "Q19": 50, "Q20": 52,
		"Q21": 54, "Q22": 56, "Q23": 58, "Q24": 60, "Q25": 62, "Q26": 64, "Q27": 66, "Q28": 68, "Q29.1": 70, "Q29.2": 71, "Q30": 72,
		"Q31.1": 73, "Q31.2": 74, "Q32.1": 75, "Q32.2": 76, "Q33.1": 77, "Q33.2": 78, "Q34.1": 79, "Q34.2": 80, "Q35.1": 81, "Q35.2": 82, "Q36.1": 83, "Q36.2": 84, "Q37.1": 86, "Q37.2": 87, "Q38.1": 89, "Q38.2": 90, "Q39.1": 92, "Q39.2": 93, "Q40.1": 95, "Q40.2": 96,
		"Q41.1": 98, "Q41.2": 99, "Q42.1": 101, "Q42.2": 102, "Q43.1": 103, "Q43.2": 104, "Q44.1": 106, "Q44.2": 107, "Q45.1": 109, "Q45.2": 110, "Q46.1": 111, "Q46.2": 112, "Q47.1": 114, "Q47.2": 115, "Q48.1": 117, "Q48.2": 118, "Q49.1": 119, "Q49.2": 120, "Q50.1": 121, "Q50.2": 122,
		"Q51.1": 123, "Q51.2": 124, "Q52.1": 125, "Q52.2": 126, "Q53.1": 127, "Q53.2": 128, "Q54.1": 129, "Q54.2": 130, "Q55.1": 131, "Q55.2": 132, "Q56.1": 133, "Q56.2": 134, "Q57.1": 135, "Q57.2": 136, "Q58.1": 138, "Q58.2": 139, "Q59.1": 141, "Q59.2": 142, "Q60.1": 144, "Q60.2": 145,
		"Q61.1": 146, "Q61.2": 147, "Q62.1": 148, "Q62.2": 149, "Q63.1": 150, "Q63.2": 151, "Q64.1": 152, "Q64.2": 153, "Q65.1": 154, "Q65.2": 155, "Q66.1": 156, "Q66.2": 157, "Q67.1": 158, "Q67.2": 159, "Q68.1": 160, "Q68.2": 161, "Q69.1": 162, "Q69.2": 163, "Q70.1": 164, "Q70.2": 165,
		"Q71.1": 166, "Q71.2": 167, "Q72.1": 168, "Q72.2": 169, "Q73.1": 170, "Q73.2": 171, "Q74.1": 172, "Q74.2": 173, "Q75.1": 174, "Q75.2": 175, "Q76.1": 176, "Q76.2": 177, "Q77.1": 178, "Q77.2": 179, "Q78.1": 180, "Q78.2": 181, "Q79.1": 182, "Q79.2": 183, "Q80.1": 184, "Q80.2": 185,
		"Q81.1": 186, "Q81.2": 187, "Q82.1": 188, "Q82.2": 189, "Q83.1": 190, "Q83.2": 191, "Q84.1": 192, "Q84.2": 193, "Q85.1": 194, "Q85.2": 195, "Q86": 196, "Q87": 197, "Q88.1": 198, "Q88.2": 199, "Q89.1": 200, "Q89.2": 201, "Q90.1": 202, "Q90.2": 203,
		"Q91.1": 204, "Q91.2": 205, "Q92.1": 206, "Q92.2": 207, "Q93.1": 208, "Q93.2": 209
	})

# 2015 ADOS1
instrument = "ADOS_Module1"
filename = "AGRE_2015/ADOS Mod1/ADOS11.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[16]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
		"family": lambda x: x[10]
	}, 
	{
		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, 
		"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": 37, "QB11": 38, "QB12": 39, "QB13.1": 40, "QB13.2": 41, "QB14": 42, "QB15": 43, "QB16": 44,
		"QC01": 45, "QC02": 46, 
		"QD01": 47, "QD02": 48, "QD03": 49, "QD04": 50, 
		"QE01": 51, "QE02": 52, "QE03": 53
	})

# 2010 ADOS1
filename = "AGRE_2010/ADOS Module 1/ADOS11.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
		"family": lambda x: x[7]
	}, 
	{
		"QA01": 18, "QA02": 19, "QA03": 20, "QA04": 21, "QA05": 22, "QA06": 23, "QA07": 24, "QA08": 25, 
		"QB01": 26, "QB02": 27, "QB03": 28, "QB04": 29, "QB05": 30, "QB06": 31, "QB07": 32, "QB08": 33, "QB09": 34, "QB10": 35, "QB11": 36, "QB12": 37, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
		"QC01": 38, "QC02": 39, 
		"QD01": 40, "QD02": 41, "QD03": 42, "QD04": 43, 
		"QE01": 44, "QE02": 45, "QE03": 46
	})

# 2015 ADOS2
instrument = "ADOS_Module2"
filename = "AGRE_2015/ADOS Mod2/ADOS21.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[16]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
		"family": lambda x: x[10]
	}, 
	{
		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, 
		"QB01": 27, "QB02": 28, "QB03": 29, "QB04": 30, "QB05": 31, "QB06": 32, "QB07": 33, "QB08": 34, "QB09.1": 35, "QB09.2": 36, "QB10": 37, "QB11": 38, "QB12": 39,
		"QC01": 40, "QC02": 41, 
		"QD01": 42, "QD02": 43, "QD03": 44, "QD04": 45, 
		"QE01": 46, "QE02": 47, "QE03": 48
	})

# 2010 ADOS2
filename = "AGRE_2010/ADOS Module 2/ADOS21.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
		"family": lambda x: x[7]
	},  
	{
		"QA01": 18, "QA02": 20, "QA03": 21, "QA04": 22, "QA05": 23, "QA06": 24, "QA07": 25, 
		"QB01": 26, "QB02": 27, "QB03": 28, "QB04": 29, "QB05": 30, "QB06": 31, "QB07": 32, "QB08": 33, "QB09.1": None, "QB09.2": None, "QB10": 34, "QB11": 35, "QB12": 36,
		"QC01": 37, "QC02": 38, 
		"QD01": 39, "QD02": 40, "QD03": 41, "QD04": 42, 
		"QE01": 43, "QE02": 44, "QE03": 45
	})

# 2015 ADOS3
instrument = "ADOS_Module3"
filename = "AGRE_2015/ADOS Mod3/ADOS31.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[16]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
		"family": lambda x: x[10]
	}, 
	{
		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, "QA09": 28, 
		"QB01": 29, "QB02": 30, "QB03": 31, "QB04": 32, "QB05": 33, "QB06": 34, "QB07": 35, "QB08": 36, "QB09": 37, "QB10": 38, "QB11": 39,
		"QC01": 40,
		"QD01": 41, "QD02": 42, "QD03": 43, "QD04": 44, "QD05": 45,
		"QE01": 46, "QE02": 47, "QE03": 48
	})

# 2010 ADOS3
filename = "AGRE_2010/ADOS Module 3/ADOS31.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
		"family": lambda x: x[7]
	},  
	{
		"QA01": 18, "QA02": 19, "QA03": 20, "QA04": 21, "QA05": 22, "QA06": 23, "QA07": 24, "QA08": 25, "QA09": 26, 
		"QB01": 27, "QB02": 28, "QB03": 29, "QB04": 30, "QB05": 31, "QB06": 32, "QB07": 33, "QB08": None, "QB09": 34, "QB10": 35, "QB11": 36,
		"QC01": 37, 
		"QD01": 38, "QD02": 39, "QD03": 40, "QD04": 41, "QD05": 42,
		"QE01": 43, "QE02": 44, "QE03": 45
	})

# 2015 ADOS4
instrument = "ADOS_Module4"
filename = "AGRE_2015/ADOS Mod4/ADOS41.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[16]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
		"family": lambda x: x[10]
	}, 
	{
		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, "QA09": 28, "QA10": 29, 
		"QB01": 30, "QB02": 31, "QB03": 32, "QB04": 33, "QB05": 34, "QB06": 35, "QB07": 36, "QB08": 37, "QB09": 38, "QB10": 39, "QB11": 40, "QB12": 41, "QB13": 42,
		"QC01": 43,
		"QD01": 44, "QD02": 45, "QD03": 46, "QD04": 47, "QD05": 48,
		"QE01": 49, "QE02": 50, "QE03": 51
	})

# 2010 ADOS4
filename = "AGRE_2010/ADOS Module 4/ADOS41.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[6],
		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
		"family": lambda x: x[7]
	},  
	{
		"QA01": 18, "QA02": 19, "QA03": 20, "QA04": 21, "QA05": 22, "QA06": 23, "QA07": 24, "QA08": 25, "QA09": 26, "QA10": 27, 
		"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": None, "QB11": 37, "QB12": 38, "QB13": 39,
		"QC01": 40, 
		"QD01": 41, "QD02": 42, "QD03": 43, "QD04": 44, "QD05": 45,
		"QE01": 46, "QE02": 47, "QE03": 48
	})

# Medical History
instrument = "Medical History"
filename = "%s/%s" % (directory, "AGRE_2015/secondary_diagnoses.txt")
print("Importing %s" % filename)

# Import diagnosis categories
diagnosis_to_category = dict()
with open( "%s/%s" % (directory, "AGRE_2015/secondary_diagnoses_categories.txt")) as f:
	for line in f:
		pieces = line.strip().split("\t")
		diagnosis_to_category[pieces[0].lower()] = pieces[1]

# Pull medical histories and insert them into schema
not_found = set()
with open(filename) as f:
	next(f)
	for line in f:
		pieces = line.split("\t")
		if (dataset, pieces[0]) in identifier_to_samples:
			sample = identifier_to_samples[(dataset, pieces[0])]
			sample[instrument] = {
				"ID": 0,
				"Seizures": 0,
				"Tourette or Tic Disorder": 0,
				"Mood Disorder": 0,
				"Anxiety Disorder": 0,
				"Psychotic Disorder": 0,
				"Autoimmune/Allergic": 0,
				"Behavior": 0,
			}
			for secondary_diagnosis in pieces[1].strip().lower().split('; '):
				if secondary_diagnosis in diagnosis_to_category:
					sample[instrument][diagnosis_to_category[secondary_diagnosis]] = 1
				else:
					not_found.add(secondary_diagnosis)

# print("Secondary diagnoses not found:", sorted(not_found))

# ***************************************************************************************************************
# *
# --------------------------------------------------- AC ------------------------------------------------------
# *
# ***************************************************************************************************************

# ADIR
dataset = "Autism Consortium"
instrument = "ADIR"
filename = "Autism_Consortium_Data/All_Measures/ADI_R.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
		"race": lambda x: x[2],
		"ethnicity": lambda x: x[3],
		"age": lambda x: int(round(float(x[8]), 0)),
		"interview_date": lambda x: x[10],
		"family": lambda x: x[0][0:x[0].rfind("-")]
	}, 
	{
		"Q02": (36, 37), "Q04": 39, "Q05": (40, 41), "Q06": (42, 43), "Q07": (44, 45), "Q08": (46, 47), "Q09": (48, 49), "Q10": (50, 51),
		"Q11": 52, "Q12": 53, "Q13": 54, "Q14": 55, "Q15": 56, "Q16": 57, "Q17": (58, 59), "Q18": 60, "Q19": (62, 63), "Q20": 64,
		"Q21": 65, "Q22": 66, "Q23": 67, "Q24": 68, "Q25": 69, "Q26": (70, 71), "Q27": 72, "Q28": (74, 75), "Q29.1": 76, "Q29.2": 77, "Q30": 78,
		"Q31.1": 79, "Q31.2": 80, "Q32.1": 81, "Q32.2": 82, "Q33.1": 83, "Q33.2": 84, "Q34.1": 85, "Q34.2": 86, "Q35.1": 87, "Q35.2": 88, "Q36.1": 89, "Q36.2": 90, "Q37.1": 91, "Q37.2": 92, "Q38.1": 93, "Q38.2": 94, "Q39.1": 95, "Q39.2": 96, "Q40.1": 97, "Q40.2": 98,
		"Q41.1": 99, "Q41.2": 100, "Q42.1": 101, "Q42.2": 102, "Q43.1": 103, "Q43.2": 104, "Q44.1": 105, "Q44.2": 106, "Q45.1": 107, "Q45.2": 108, "Q46.1": 109, "Q46.2": 110, "Q47.1": 111, "Q47.2": 112, "Q48.1": 113, "Q48.2": 114, "Q49.1": 115, "Q49.2": 116, "Q50.1": 117, "Q50.2": 118,
		"Q51.1": 119, "Q51.2": 120, "Q52.1": 121, "Q52.2": 122, "Q53.1": 123, "Q53.2": 124, "Q54.1": 125, "Q54.2": 126, "Q55.1": 127, "Q55.2": 128, "Q56.1": 129, "Q56.2": 130, "Q57.1": 131, "Q57.2": 132, "Q58.1": 134, "Q58.2": 135, "Q59.1": 136, "Q59.2": 137, "Q60.1": 140, "Q60.2": 141,
		"Q61.1": 142, "Q61.2": 143, "Q62.1": 144, "Q62.2": 145, "Q63.1": 146, "Q63.2": 147, "Q64.1": 148, "Q64.2": 149, "Q65.1": 150, "Q65.2": 151, "Q66.1": 152, "Q66.2": 153, "Q67.1": 154, "Q67.2": 155, "Q68.1": 156, "Q68.2": 157, "Q69.1": 158, "Q69.2": 159, "Q70.1": 160, "Q70.2": 161,
		"Q71.1": 162, "Q71.2": 163, "Q72.1": 164, "Q72.2": 165, "Q73.1": 166, "Q73.2": 167, "Q74.1": 168, "Q74.2": 169, "Q75.1": 170, "Q75.2": 171, "Q76.1": 172, "Q76.2": 173, "Q77.1": 175, "Q77.2": 175, "Q78.1": 176, "Q78.2": 177, "Q79.1": 178, "Q79.2": 179, "Q80.1": 180, "Q80.2": 181,
		"Q81.1": 182, "Q81.2": 183, "Q82.1": 184, "Q82.2": 185, "Q83.1": 186, "Q83.2": 187, "Q84.1": 188, "Q84.2": 189, "Q85.1": 190, "Q85.2": 191, "Q86": 192, "Q87": 193, "Q88.1": 194, "Q88.2": 195, "Q89.1": 196, "Q89.2": 197, "Q90.1": 198, "Q90.2": 199,
		"Q91.1": 200, "Q91.2": 201, "Q92.1": 202, "Q92.2": 203, "Q93.1": 204, "Q93.2": 205
	})

# ADOS1
instrument = "ADOS_Module1"
filename = "Autism_Consortium_Data/All_Measures/ADOS_Module_1.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
		"race": lambda x: x[2],
		"ethnicity": lambda x: x[3],
		"age": lambda x: int(round(float(x[8]), 0)),
		"interview_date": lambda x: x[10],
		"family": lambda x: x[0][0:x[0].rfind("-")]
	}, 
	{
		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, 
		"QB01": 19, "QB02": 20, "QB03": 21, "QB04": 22, "QB05": 23, "QB06": 24, "QB07": 25, "QB08": 26, "QB09": 27, "QB10": 28, "QB11": 29, "QB12": 30, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
		"QC01": 31, "QC02": 32, 
		"QD01": 33, "QD02": 35, "QD03": 37, "QD04": 38, 
		"QE01": 40, "QE02": 41, "QE03": 42
	})

# ADOS2
instrument = "ADOS_Module2"
filename = "Autism_Consortium_Data/All_Measures/ADOS_Module_2.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
		"race": lambda x: x[2],
		"ethnicity": lambda x: x[3],
		"age": lambda x: int(round(float(x[8]), 0)),
		"interview_date": lambda x: x[10],
		"family": lambda x: x[0][0:x[0].rfind("-")]
	},   
	{
		"QA01": 11, "QA02": 13, "QA03": 14, "QA04": 15, "QA05": 16, "QA06": 17, "QA07": 18, 
		"QB01": 19, "QB02": 20, "QB03": 21, "QB04": 22, "QB05": 23, "QB06": 24, "QB07": 25, "QB08": 26, "QB09.1": None, "QB09.2": None, "QB10": 27, "QB11": 28, "QB12": 29,
		"QC01": 30, "QC02": 31, 
		"QD01": 32, "QD02": 34, "QD03": 36, "QD04": 37, 
		"QE01": 39, "QE02": 40, "QE03": 41
	})

# ADOS3
instrument = "ADOS_Module3"
filename = "Autism_Consortium_Data/All_Measures/ADOS_Module_3.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
		"race": lambda x: x[2],
		"ethnicity": lambda x: x[3],
		"age": lambda x: int(round(float(x[8]), 0)),
		"interview_date": lambda x: x[10],
		"family": lambda x: x[0][0:x[0].rfind("-")]
	},   
	{
		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, "QA09": 19, 
		"QB01": 20, "QB02": 21, "QB03": 22, "QB04": 23, "QB05": 24, "QB06": 25, "QB07": 26, "QB08": None, "QB09": 27, "QB10": 28, "QB11": 29,
		"QC01": 30,
		"QD01": 31, "QD02": 33, "QD03": 35, "QD04": 36, "QD05": 37, 
		"QE01": 39, "QE02": 40, "QE03": 41
	})

# ADOS4
instrument = "ADOS_Module4"
filename = "Autism_Consortium_Data/All_Measures/ADOS_Module_4.csv"

convert_phenotypes(filename, dataset, instrument,
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
		"race": lambda x: x[2],
		"ethnicity": lambda x: x[3],
		"age": lambda x: int(round(float(x[8]), 0)),
		"interview_date": lambda x: x[10],
		"family": lambda x: x[0][0:x[0].rfind("-")]
	},   
	{
		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, "QA09": 19, "QA10": 20, 
		"QB01": 21, "QB02": 22, "QB03": 23, "QB04": 24, "QB05": 25, "QB06": 26, "QB07": 27, "QB08": 28, "QB09": 29, "QB10": None, "QB11": 30, "QB12": 31, "QB13": 32,
		"QC01": 33,
		"QD01": 34, "QD02": 36, "QD03": 38, "QD04": 39, "QD05": 40, 
		"QE01": 42, "QE02": 45, "QE03": 44
	})

# ***************************************************************************************************************
# *
# --------------------------------------------------- NDAR ------------------------------------------------------
# *
# ***************************************************************************************************************

# ADIR
dataset = "National Database for Autism Research"
instrument = "ADIR"

path = "ndar.phenotype.collection"
for filename in os.listdir("%s/%s" % (directory, path)):
	subpath = os.path.join(path, filename)

	# If we see a directory, and it has an adir file, then read it
	filename = os.path.join(subpath, "adi_200304.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[22] == "M" else ("Female" if x[22] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[3]), 0)),
				"interview_date": lambda x: x[5],
				"family": lambda x: None
			}, 
			{
				"Q02": 26, "Q04": 28, "Q05": 31, "Q06": 33, "Q07": 34, "Q08": 35, "Q09": 37, "Q10": 41,
				"Q11": 43, "Q12": 44, "Q13": 45, "Q14": 46, "Q15": 47, "Q16": 48, "Q17": 49, "Q18": 50, "Q19": 53, "Q20": 54,
				"Q21": 55, "Q22": 56, "Q23": 57, "Q24": 58, "Q25": 59, "Q26": 61, "Q27": 62, "Q28": 63, "Q29.1": 64, "Q29.2": 65, "Q30": 67,
				"Q31.1": 68, "Q31.2": 69, "Q32.1": 70, "Q32.2": 71, "Q33.1": 72, "Q33.2": 73, "Q34.1": 74, "Q34.2": 75, "Q35.1": 76, "Q35.2": 77, "Q36.1": 78, "Q36.2": 79, "Q37.1": 81, "Q37.2": 82, "Q38.1": 84, "Q38.2": 85, "Q39.1": 87, "Q39.2": 88, "Q40.1": 91, "Q40.2": 92,
				"Q41.1": 94, "Q41.2": 95, "Q42.1": 97, "Q42.2": 98, "Q43.1": 99, "Q43.2": 100, "Q44.1": 102, "Q44.2": 103, "Q45.1": 105, "Q45.2": 106, "Q46.1": 107, "Q46.2": 108, "Q47.1": 110, "Q47.2": 111, "Q48.1": 113, "Q48.2": 114, "Q49.1": 116, "Q49.2": 117, "Q50.1": 118, "Q50.2": 119,
				"Q51.1": 120, "Q51.2": 121, "Q52.1": 122, "Q52.2": 123, "Q53.1": 124, "Q53.2": 125, "Q54.1": 126, "Q54.2": 127, "Q55.1": 128, "Q55.2": 129, "Q56.1": 130, "Q56.2": 131, "Q57.1": 133, "Q57.2": 134, "Q58.1": 136, "Q58.2": 137, "Q59.1": 139, "Q59.2": 140, "Q60.1": 154, "Q60.2": 155,
				"Q61.1": 157, "Q61.2": 158, "Q62.1": 159, "Q62.2": 160, "Q63.1": 161, "Q63.2": 162, "Q64.1": 163, "Q64.2": 164, "Q65.1": 165, "Q65.2": 166, "Q66.1": 168, "Q66.2": 169, "Q67.1": 171, "Q67.2": 172, "Q68.1": 173, "Q68.2": 174, "Q69.1": 176, "Q69.2": 177, "Q70.1": 178, "Q70.2": 179,
				"Q71.1": 181, "Q71.2": 182, "Q72.1": 184, "Q72.2": 185, "Q73.1": 186, "Q73.2": 187, "Q74.1": 189, "Q74.2": 190, "Q75.1": 192, "Q75.2": 193, "Q76.1": 195, "Q76.2": 196, "Q77.1": 198, "Q77.2": 199, "Q78.1": 201, "Q78.2": 202, "Q79.1": 204, "Q79.2": 205, "Q80.1": 206, "Q80.2": 207,
				"Q81.1": 209, "Q81.2": 210, "Q82.1": 212, "Q82.2": 213, "Q83.1": 215, "Q83.2": 216, "Q84.1": 218, "Q84.2": 219, "Q85.1": 220, "Q85.2": 221, "Q86": 223, "Q87": 224, "Q88.1": 225, "Q88.2": 226, "Q89.1": 227, "Q89.2": 228, "Q90.1": 229, "Q90.2": 230,
				"Q91.1": 231, "Q91.2": 232, "Q92.1": 233, "Q92.2": 234, "Q93.1": 235, "Q93.2": 236
			}, num_headers=2, delimiter='\t')

	# This is an alternative adir format, found in the ndar dataset
	filename = os.path.join(subpath, "adi_c02.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: None if x[5] == '' else int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"Q02": 13, "Q04": 12, "Q05": 14, "Q06": 15, "Q07": 16, "Q08": 17, "Q09": 18, "Q10": 19,
				"Q11": 20, "Q12": 21, "Q13": 22, "Q14": 23, "Q15": 24, "Q16": 25, "Q17": 26, "Q18": 27, "Q19": 28, "Q20": 29,
				"Q21": 30, "Q22": 31, "Q23": 32, "Q24": 33, "Q25": None, "Q26": 34, "Q27": 35, "Q28": None, "Q29.1": 36, "Q29.2": 37, "Q30": 38,
				"Q31.1": 39, "Q31.2": 40, "Q32.1": 41, "Q32.2": 42, "Q33.1": 43, "Q33.2": 44, "Q34.1": 45, "Q34.2": None, "Q35.1": None, "Q35.2": None, "Q36.1": 46, "Q36.2": 47, "Q37.1": 48, "Q37.2": 49, "Q38.1": 50, "Q38.2": 51, "Q39.1": 52, "Q39.2": 53, "Q40.1": 54, "Q40.2": 55,
				"Q41.1": 56, "Q41.2": 57, "Q42.1": 58, "Q42.2": 59, "Q43.1": 60, "Q43.2": 61, "Q44.1": 62, "Q44.2": 63, "Q45.1": 64, "Q45.2": 65, "Q46.1": 66, "Q46.2": 67, "Q47.1": 68, "Q47.2": 69, "Q48.1": 70, "Q48.2": 71, "Q49.1": 72, "Q49.2": 73, "Q50.1": 74, "Q50.2": 75,
				"Q51.1": 76, "Q51.2": 77, "Q52.1": 78, "Q52.2": 79, "Q53.1": 80, "Q53.2": 81, "Q54.1": 82, "Q54.2": 83, "Q55.1": 84, "Q55.2": 85, "Q56.1": 86, "Q56.2": 87, "Q57.1": 88, "Q57.2": 89, "Q58.1": 90, "Q58.2": 91, "Q59.1": 92, "Q59.2": 93, "Q60.1": 94, "Q60.2": 95,
				"Q61.1": 96, "Q61.2": 97, "Q62.1": 98, "Q62.2": 99, "Q63.1": 100, "Q63.2": 101, "Q64.1": 102, "Q64.2": 103, "Q65.1": 104, "Q65.2": 105, "Q66.1": 106, "Q66.2": 107, "Q67.1": 108, "Q67.2": 109, "Q68.1": 110, "Q68.2": 111, "Q69.1": 112, "Q69.2": 113, "Q70.1": 114, "Q70.2": 115,
				"Q71.1": 116, "Q71.2": 117, "Q72.1": 118, "Q72.2": 119, "Q73.1": 120, "Q73.2": None, "Q74.1": 121, "Q74.2": 122, "Q75.1": 123, "Q75.2": 124, "Q76.1": 125, "Q76.2": 126, "Q77.1": 127, "Q77.2": 128, "Q78.1": 129, "Q78.2": 130, "Q79.1": 131, "Q79.2": 132, "Q80.1": 133, "Q80.2": 134,
				"Q81.1": 135, "Q81.2": 136, "Q82.1": 137, "Q82.2": 138, "Q83.1": 139, "Q83.2": 140, "Q84.1": 141, "Q84.2": 142, "Q85.1": 143, "Q85.2": 144, "Q86": 145, "Q87": 146, "Q88.1": None, "Q88.2": None, "Q89.1": None, "Q89.2": None, "Q90.1": None, "Q90.2": None,
				"Q91.1": None, "Q91.2": None, "Q92.1": None, "Q92.2": None, "Q93.1": None, "Q93.2": None
			}, num_headers=2, delimiter='\t')

# ADOS1
instrument = "ADOS_Module1"

for filename in os.listdir("%s/%s" % (directory, path)):
	subpath = os.path.join(path, filename)

	# If we see a directory, and it has an ados file, then read it
	filename = os.path.join(subpath, "ados1_200102.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 53, "QA02": 54, "QA03": 55, "QA04": 56, "QA05": 57, "QA06": 58, "QA07": 59, "QA08": 60, 
				"QB01": 61, "QB02": 62, "QB03": 63, "QB04": 64, "QB05": 65, "QB06": 66, "QB07": 67, "QB08": 68, "QB09": 69, "QB10": 70, "QB11": 71, "QB12": 72, "QB13.1": None, "QB13.2": None, "QB14": None, "QB14": None, "QB15": None, "QB16": None,
				"QC01": 73, "QC02": 74, 
				"QD01": 75, "QD02": 77, "QD03": 79, "QD04": 80, 
				"QE01": 82, "QE02": 83, "QE03": 84
			}, num_headers=2, delimiter='\t')
	
	# Alternative file format
	filename = os.path.join(subpath, "ados1_200701.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			},
			{
				"QA01": 53, "QA02": 54, "QA03": 55, "QA04": 56, "QA05": 57, "QA06": 58, "QA07": 59, "QA08": 60, 
				"QB01": 61, "QB02": 62, "QB03": 63, "QB04": 64, "QB05": 65, "QB06": 66, "QB07": 67, "QB08": 68, "QB09": 69, "QB10": 70, "QB11": 71, "QB12": 72, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
				"QC01": 73, "QC02": 74, 
				"QD01": 75, "QD02": 77, "QD03": 79, "QD04": 80, 
				"QE01": 82, "QE02": 83, "QE03": 84
			}, num_headers=2, delimiter='\t')

	# Alternative file format
	filename = os.path.join(subpath, "ados1_201201.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, 
				"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": 37, "QB11": 38, "QB12": 39, "QB13.1": 40, "QB13.2": 41, "QB14": 42, "QB15": 43, "QB16": 44,
				"QC01": 45, "QC02": 46, 
				"QD01": 47, "QD02": 49, "QD03": 41, "QD04": 42, 
				"QE01": 54, "QE02": 55, "QE03": 56
			}, num_headers=2, delimiter='\t')

# ADOS2
instrument = "ADOS_Module2"

for filename in os.listdir("%s/%s" % (directory, path)):
	subpath = os.path.join(path, filename)

	# If we see a directory, and it has an ados file, then read it
	filename = os.path.join(subpath, "ados2_200102.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 40, "QA02": 42, "QA03": 43, "QA04": 44, "QA05": 45, "QA06": 46, "QA07": 47, 
				"QB01": 48, "QB02": 49, "QB03": 50, "QB04": 51, "QB05": 52, "QB06": 53, "QB07": 54, "QB08": 55, "QB09.1": None, "QB09.2": None, "QB10": 56, "QB11": 57, "QB12": 58,
				"QC01": 59, "QC02": 60, 
				"QD01": 61, "QD02": 63, "QD03": 65, "QD04": 66, 
				"QE01": 68, "QE02": 69, "QE03": 70
			}, num_headers=2, delimiter='\t')
	
	# Alternative file format
	filename = os.path.join(subpath, "ados2_200701.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 40, "QA02": 42, "QA03": 43, "QA04": 44, "QA05": 45, "QA06": 46, "QA07": 47, 
				"QB01": 48, "QB02": 49, "QB03": 50, "QB04": 51, "QB05": 52, "QB06": 53, "QB07": 54, "QB08": 55, "QB09.1": None, "QB09.2": None, "QB10": 56, "QB11": 57, "QB12": 58,
				"QC01": 59, "QC02": 60, 
				"QD01": 61, "QD02": 63, "QD03": 65, "QD04": 66, 
				"QE01": 68, "QE02": 69, "QE03": 70
			}, num_headers=2, delimiter='\t')

	# Alternative file format
	filename = os.path.join(subpath, "ados2_201201.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, 
				"QB01": 31, "QB02": 32, "QB03": 33, "QB04": 34, "QB05": 35, "QB06": 36, "QB07": 37, "QB08": 38, "QB09.1": 39, "QB09.2": 40, "QB10": 41, "QB11": 42, "QB12": 43,
				"QC01": 44, "QC02": 45, 
				"QD01": 46, "QD02": 47, "QD03": 48, "QD04": 49, 
				"QE01": 50, "QE02": 51, "QE03": 52
			}, num_headers=2, delimiter='\t')

# ADOS3
instrument = "ADOS_Module3"

for filename in os.listdir("%s/%s" % (directory, path)):
	subpath = os.path.join(path, filename)

	# If we see a directory, and it has an ados file, then read it
	filename = os.path.join(subpath, "ados3_200102.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31, 
				"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": None, "QB09": 29, "QB10": 40, "QB11": 41,
				"QC01": 42, 
				"QD01": 43, "QD02": 45, "QD03": 47, "QD04": 48,  "QD05": 49,
				"QE01": 51, "QE02": 52, "QE03": 53
			}, num_headers=2, delimiter='\t')
	
	# Alternative file format
	filename = os.path.join(subpath, "ados3_200701.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31, 
				"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": None, "QB09": 29, "QB10": 40, "QB11": 41,
				"QC01": 42, 
				"QD01": 43, "QD02": 45, "QD03": 47, "QD04": 48,  "QD05": 49,
				"QE01": 51, "QE02": 52, "QE03": 53
			}, num_headers=2, delimiter='\t')

	# Alternative file format
	filename = os.path.join(subpath, "ados3_201201.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31,   
				"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": 39, "QB09": 40, "QB10": 41, "QB11": 42,
				"QC01": 43, 
				"QD01": 44, "QD02": 46, "QD03": 48, "QD04": 49, "QD05": 50,
				"QE01": 52, "QE02": 53, "QE03": 54
			}, num_headers=2, delimiter='\t')

# ADOS4
instrument = "ADOS_Module4"

for filename in os.listdir("%s/%s" % (directory, path)):
	subpath = os.path.join(path, filename)

	# If we see a directory, and it has an ados file, then read it
	filename = os.path.join(subpath, "ados4_200102.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, "QA08": 31, "QA09": 32, "QA10": 33, 
				"QB01": 34, "QB02": 35, "QB03": 36, "QB04": 37, "QB05": 38, "QB06": 39, "QB07": 40, "QB08": 41, "QB09": 42, "QB10": None, "QB11": 43, "QB12": 44, "QB13": 45,
				"QC01": 46, 
				"QD01": 47, "QD02": 49, "QD03": 51, "QD04": 52,  "QD05": 53,
				"QE01": 55, "QE02": 56, "QE03": 57
			}, num_headers=2, delimiter='\t')

	# Alternative file format
	filename = os.path.join(subpath, "ados4_201201.txt")
	if os.path.isdir("%s/%s" % (directory, subpath)) and os.path.isfile("%s/%s" % (directory, filename)):
		convert_phenotypes(filename, dataset, instrument, 
			{
				"identifier": lambda x: x[2],
				"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
				"race": lambda x: None,
				"ethnicity": lambda x: None,
				"age": lambda x: int(round(float(x[5]), 0)),
				"interview_date": lambda x: x[4],
				"family": lambda x: None
			}, 
			{
				"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, "QA08": 31, "QA09": 32, "QA10": 33, 
				"QB01": 34, "QB02": 35, "QB03": 36, "QB04": 37, "QB05": 38, "QB06": 39, "QB07": 40, "QB08": 41, "QB09": 42, "QB10": 43, "QB11": 44, "QB12": 45, "QB13": 46,
				"QC01": 47, 
				"QD01": 48, "QD02": 50, "QD03": 52, "QD04": 53,  "QD05": 54,
				"QE01": 56, "QE02": 57, "QE03": 58
			}, num_headers=2, delimiter='\t')

# ***************************************************************************************************************
# *
# --------------------------------------------------- SSC ------------------------------------------------------
# *
# ***************************************************************************************************************

# ADIR Proband
dataset = "Simons Simplex Collection"
instrument = "ADIR"
filename = "SSC Version 15 Phenotype Data Set 2/Proband Data/adi_r.csv"

convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"Q02": (2, 3), "Q04": 4, "Q05": (5, 6), "Q06": (7, 8), "Q07": (9, 10), "Q08": (11, 12), "Q09": (13, 14), "Q10": (15, 16),
		"Q11": 17, "Q12": 18, "Q13": 19, "Q14": 20, "Q15": 21, "Q16": 22, "Q17": (23, 24), "Q18": 25, "Q19": (26, 27), "Q20": 28,
		"Q21": 29, "Q22": 30, "Q23": 31, "Q24": 32, "Q25": 33, "Q26": (34, 35), "Q27": 36, "Q28": (37, 38), "Q29.1": 39, "Q29.2": 40, "Q30": 41,
		"Q31.1": 42, "Q31.2": 43, "Q32.1": 44, "Q32.2": 45, "Q33.1": 46, "Q33.2": 47, "Q34.1": 48, "Q34.2": 49, "Q35.1": 50, "Q35.2": 51, "Q36.1": 52, "Q36.2": 53, "Q37.1": 54, "Q37.2": 55, "Q38.1": 56, "Q38.2": 57, "Q39.1": 58, "Q39.2": 59, "Q40.1": 60, "Q40.2": 61,
		"Q41.1": 62, "Q41.2": 63, "Q42.1": 64, "Q42.2": 65, "Q43.1": 66, "Q43.2": 67, "Q44.1": 68, "Q44.2": 69, "Q45.1": 70, "Q45.2": 71, "Q46.1": 72, "Q46.2": 73, "Q47.1": 74, "Q47.2": 75, "Q48.1": 76, "Q48.2": 77, "Q49.1": 78, "Q49.2": 79, "Q50.1": 80, "Q50.2": 81,
		"Q51.1": 82, "Q51.2": 83, "Q52.1": 84, "Q52.2": 85, "Q53.1": 86, "Q53.2": 87, "Q54.1": 88, "Q54.2": 89, "Q55.1": 90, "Q55.2": 91, "Q56.1": 92, "Q56.2": 93, "Q57.1": 94, "Q57.2": 95, "Q58.1": 96, "Q58.2": 97, "Q59.1": 98, "Q59.2": 99, "Q60.1": 100, "Q60.2": 101,
		"Q61.1": 102, "Q61.2": 103, "Q62.1": 104, "Q62.2": 105, "Q63.1": 106, "Q63.2": 107, "Q64.1": 108, "Q64.2": 109, "Q65.1": 110, "Q65.2": 111, "Q66.1": 112, "Q66.2": 113, "Q67.1": 114, "Q67.2": 115, "Q68.1": 116, "Q68.2": 117, "Q69.1": 118, "Q69.2": 119, "Q70.1": 120, "Q70.2": 121,
		"Q71.1": 122, "Q71.2": 123, "Q72.1": 124, "Q72.2": 125, "Q73.1": 126, "Q73.2": 127, "Q74.1": 128, "Q74.2": 129, "Q75.1": 130, "Q75.2": 131, "Q76.1": 132, "Q76.2": 133, "Q77.1": 134, "Q77.2": 135, "Q78.1": 136, "Q78.2": 137, "Q79.1": 138, "Q79.2": 139, "Q80.1": 140, "Q80.2": 141,
		"Q81.1": 142, "Q81.2": 143, "Q82.1": 144, "Q82.2": 145, "Q83.1": 146, "Q83.2": 147, "Q84.1": 148, "Q84.2": 149, "Q85.1": 150, "Q85.2": 151, "Q86": 152, "Q87": (153, 154), "Q88.1": 155, "Q88.2": 156, "Q89.1": 157, "Q89.2": 158, "Q90.1": 159, "Q90.2": 160,
		"Q91.1": 161, "Q91.2": 162, "Q92.1": 163, "Q92.2": 164, "Q93.1": 165, "Q93.2": 166
	})

# ADIR Twins
filename = "SSC Version 15 Phenotype Data Set 2/MZ Twin Data/adi_r.csv"

convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"Q02": (2, 3), "Q04": 4, "Q05": (5, 6), "Q06": (7, 8), "Q07": (9, 10), "Q08": (11, 12), "Q09": (13, 14), "Q10": (15, 16),
		"Q11": 17, "Q12": 18, "Q13": 19, "Q14": 20, "Q15": 21, "Q16": 22, "Q17": (23, 24), "Q18": 25, "Q19": (26, 27), "Q20": 28,
		"Q21": 29, "Q22": 30, "Q23": 31, "Q24": 32, "Q25": 33, "Q26": (34, 35), "Q27": 36, "Q28": (37, 38), "Q29.1": 39, "Q29.2": 40, "Q30": 41,
		"Q31.1": 42, "Q31.2": 43, "Q32.1": 44, "Q32.2": 45, "Q33.1": 46, "Q33.2": 47, "Q34.1": 48, "Q34.2": 49, "Q35.1": 50, "Q35.2": 51, "Q36.1": 52, "Q36.2": 53, "Q37.1": 54, "Q37.2": 55, "Q38.1": 56, "Q38.2": 57, "Q39.1": 58, "Q39.2": 59, "Q40.1": 60, "Q40.2": 61,
		"Q41.1": 62, "Q41.2": 63, "Q42.1": 64, "Q42.2": 65, "Q43.1": 66, "Q43.2": 67, "Q44.1": 68, "Q44.2": 69, "Q45.1": 70, "Q45.2": 71, "Q46.1": 72, "Q46.2": 73, "Q47.1": 74, "Q47.2": 75, "Q48.1": 76, "Q48.2": 77, "Q49.1": 78, "Q49.2": 79, "Q50.1": 80, "Q50.2": 81,
		"Q51.1": 82, "Q51.2": 83, "Q52.1": 84, "Q52.2": 85, "Q53.1": 86, "Q53.2": 87, "Q54.1": 88, "Q54.2": 89, "Q55.1": 90, "Q55.2": 91, "Q56.1": 92, "Q56.2": 93, "Q57.1": 94, "Q57.2": 95, "Q58.1": 96, "Q58.2": 97, "Q59.1": 98, "Q59.2": 99, "Q60.1": 100, "Q60.2": 101,
		"Q61.1": 102, "Q61.2": 103, "Q62.1": 104, "Q62.2": 105, "Q63.1": 106, "Q63.2": 107, "Q64.1": 108, "Q64.2": 109, "Q65.1": 110, "Q65.2": 111, "Q66.1": 112, "Q66.2": 113, "Q67.1": 114, "Q67.2": 115, "Q68.1": 116, "Q68.2": 117, "Q69.1": 118, "Q69.2": 119, "Q70.1": 120, "Q70.2": 121,
		"Q71.1": 122, "Q71.2": 123, "Q72.1": 124, "Q72.2": 125, "Q73.1": 126, "Q73.2": 127, "Q74.1": 128, "Q74.2": 129, "Q75.1": 130, "Q75.2": 131, "Q76.1": 132, "Q76.2": 133, "Q77.1": 134, "Q77.2": 135, "Q78.1": 136, "Q78.2": 137, "Q79.1": 138, "Q79.2": 139, "Q80.1": 140, "Q80.2": 141,
		"Q81.1": 142, "Q81.2": 143, "Q82.1": 144, "Q82.2": 145, "Q83.1": 146, "Q83.2": 147, "Q84.1": 148, "Q84.2": 149, "Q85.1": 150, "Q85.2": 151, "Q86": 152, "Q87": (153, 154), "Q88.1": 155, "Q88.2": 156, "Q89.1": 157, "Q89.2": 158, "Q90.1": 159, "Q90.2": 160,
		"Q91.1": 161, "Q91.2": 162, "Q92.1": 163, "Q92.2": 164, "Q93.1": 165, "Q93.2": 166
	})

# ADOS1 Proband
instrument = "ADOS_Module1"
filename = "SSC Version 15 Phenotype Data Set 2/Proband Data/ados_1_raw.csv"

convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, 
		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09": 18, "QB10": 19, "QB11": 20, "QB12": 21, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
		"QC01": 22, "QC02": 23, 
		"QD01": 24, "QD02": 25, "QD03": 26, "QD04": 27, 
		"QE01": 28, "QE02": 29, "QE03": 30
	})

# ADOS1 Twins
filename = "SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_1_raw.csv"

convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, 
		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09": 18, "QB10": 19, "QB11": 20, "QB12": 21, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
		"QC01": 22, "QC02": 23, 
		"QD01": 24, "QD02": 25, "QD03": 26, "QD04": 27, 
		"QE01": 28, "QE02": 29, "QE03": 30
	})

# ADOS2 Proband
instrument = "ADOS_Module2"
filename = "SSC Version 15 Phenotype Data Set 2/Proband Data/ados_2_raw.csv"
	
convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 4, "QA03": 5, "QA04": 6, "QA05": 7, "QA06": 8, "QA07": 9,
		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09.1": None, "QB09.2": None, "QB10": 18, "QB11": 19, "QB12": 20,
		"QC01": 21, "QC02": 22, 
		"QD01": 23, "QD02": 24, "QD03": 25, "QD04": 26, 
		"QE01": 27, "QE02": 28, "QE03": 29
	})

# ADOS2 Twins
filename = "SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_2_raw.csv"

convert_phenotypes(filename, dataset, instrument,  
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 4, "QA03": 5, "QA04": 6, "QA05": 7, "QA06": 8, "QA07": 9,
		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09.1": None, "QB09.2": None, "QB10": 18, "QB11": 19, "QB12": 20,
		"QC01": 21, "QC02": 22, 
		"QD01": 23, "QD02": 24, "QD03": 25, "QD04": 26, 
		"QE01": 27, "QE02": 28, "QE03": 29
	})

# ADOS3 Proband
instrument = "ADOS_Module3"
filename = "SSC Version 15 Phenotype Data Set 2/Proband Data/ados_3_raw.csv"
	
convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10,
		"QB01": 11, "QB02": 12, "QB03": 13, "QB04": 14, "QB05": 15, "QB06": 16, "QB07": 17, "QB08": None, "QB09": 18, "QB10": 19, "QB11": 20,
		"QC01": 21,
		"QD01": 22, "QD02": 23, "QD03": 24, "QD04": 25, "QD05": 26, 
		"QE01": 27, "QE02": 28, "QE03": 29
	})

# ADOS3 Twins
filename = "SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_3_raw.csv"

convert_phenotypes(filename, dataset, instrument,  
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10,
		"QB01": 11, "QB02": 12, "QB03": 13, "QB04": 14, "QB05": 15, "QB06": 16, "QB07": 17, "QB08": None, "QB09": 18, "QB10": 19, "QB11": 20,
		"QC01": 21,
		"QD01": 22, "QD02": 23, "QD03": 24, "QD04": 25, "QD05": 26, 
		"QE01": 27, "QE02": 28, "QE03": 29
	})

# ADOS4 Proband
instrument = "ADOS_Module4"
filename = "SSC Version 15 Phenotype Data Set 2/Proband Data/ados_4_raw.csv"
	
convert_phenotypes(filename, dataset, instrument, 
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10, "QA10": 11,
		"QB01": 12, "QB02": 13, "QB03": 14, "QB04": 15, "QB05": 16, "QB06": 17, "QB07": 18, "QB08": 19, "QB09": 20, "QB10": None, "QB11": 21, "QB12": 22, "QB13": 23,
		"QC01": 24,
		"QD01": 25, "QD02": 26, "QD03": 27, "QD04": 28, "QD05": 29, 
		"QE01": 30, "QE02": 31, "QE03": 32
	})

# ADOS4 Twins
filename = "SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_4_raw.csv"

convert_phenotypes(filename, dataset, instrument,  
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None,
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: None,
		"interview_date": lambda x: None,
		"family": lambda x: None
	}, 
	{
		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10, "QA10": 11,
		"QB01": 12, "QB02": 13, "QB03": 14, "QB04": 15, "QB05": 16, "QB06": 17, "QB07": 18, "QB08": 19, "QB09": 20, "QB10": None, "QB11": 21, "QB12": 22, "QB13": 23,
		"QC01": 24,
		"QD01": 25, "QD02": 26, "QD03": 27, "QD04": 28, "QD05": 29, 
		"QE01": 30, "QE02": 31, "QE03": 32
	})

# ***************************************************************************************************************
# *
# --------------------------------------------------- Write to file ------------------------------------------------------
# *
# ***************************************************************************************************************

# Remove bad samples
for sample_id in bad_samples:
	if sample_id in identifier_to_samples:
		del identifier_to_samples[sample_id]

# Create a sorted list of samples
samples = list(identifier_to_samples.values())
samples.sort(key= lambda x: (x["dataset"], x["identifier"]))

# Write json to file
with open('../data/all_samples_stage1.json', 'w+') as outfile:
	print(len(samples))
	json.dump(samples, outfile, sort_keys=True, indent=4)


