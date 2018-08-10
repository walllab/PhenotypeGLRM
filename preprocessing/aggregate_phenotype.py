# We currently have several phenotype datasets:
# Autism Genetic Resource Exchange (AGRE)
# Autism Consortium (AC)
# National Database for Autism Research (NDAR)
# Simons Simplex Collection (SSC)
# Cognoa Controls (COG)
# Simons Variation in Individuals Project (SVIP)
# Autism Speaks (MSSNG)
# Autism Genome Project (AGP)

# We're working on getting access to one more:
# Autism Treatment Network (ATN)

# Each of these datasets has collected different phenotype information about its participants,
# but most contain ADIR, ADOS, or SRS so we're starting there.

# Raw data can be found on sherlock /scratch/PI/dpwall/DATA/phenotypes

# In writing this script, I added three files to the phenotypes directory on sherlock:
# secondary_diagnoses_categories.txt - manual curation of secondary diagnoses from AGRE into categories done by Chloe
# secondary_diagnoses - manual cleanup of secondary diagnoses from AGRE done by Preston
# cognoa_adir_dataset.txt - from Cognoa

# This code requires a path to our phenotype data.
# It outputs a file called all_samples_stage1.json which contains aggregated phenotype data across our
# four datasets.
# It is meant to be run as part of a multi-stage pipeline described in the README.

# The code can be run with:
# python3 aggregate_phenotype.py path-to-phenotype-data

# Some notes
#
# -------- ADIR --------
# You can tell different versions of ADIR apart based on number of items (93=ADIR2003, 111=ADIR1995, 62=ADIR1995_Short which can be converted to ADIR1995)
# also, ADIR1995 has "arms up to be lifted" after "inappropriate facial expression", ADIR2003 doesn't have this question
# For ADIR1995, be careful of A and B responses - they're typically reversed (before, after)
# adir_t in NDAR are ADIR for toddlers - we don't have items for that instrument yet.

import json
import jsonschema
import csv
import os
import sys

# Load schema
with open('schemas/Individual.json') as schema_file:    
	pheno_schema = json.load(schema_file)

# For each instrument, pull coded feature values from the schema
instrument_to_codes = {}
for instrument in [k for k, v in pheno_schema['properties'].items() if 'type' in v and v['type'] == 'object']:
	instrument_to_codes[instrument] = {}
	with open('schemas/%s.json' % instrument) as instrument_schema_file:
		instrument_schema = json.load(instrument_schema_file)
		for feature in instrument_schema['properties'].keys():
			if feature.startswith('Q') and not feature.endswith('a'):
				# If it has an 'a' counterpart, then it contains coded values
				if feature + 'a' in instrument_schema['properties']:
					coded_values = instrument_schema['properties'][feature + 'a']['enum'][:]
					coded_values.remove(None)
					coded_values.remove(0)
					instrument_to_codes[instrument][feature] = set(coded_values)
				else:
					instrument_to_codes[instrument][feature] = None

def print_codes_for_instrument(instrument):
	items = []
	with open('schemas/%s.json' % instrument) as instrument_schema_file:
		instrument_schema = json.load(instrument_schema_file)
		for feature in instrument_schema['properties'].keys():
			if feature.startswith('Q') and not feature.endswith('a'):
				items.append(feature)
	print(items)

# These are entry errors in our datasets that need to be taken care of
instrument_to_exceptions = {
	"ADIR1995" : {
		"Q019": {'5': None, '9': None},
		"Q030": {'3': None},
		"Q030E": {'3': None},
		"Q034A": {'8': None, '9': None},
		"Q034AE": {'8': None, '9': None},
		"Q079": {'8': None},
		"Q079E": {'8': None},
		"Q097A5": {'8': None},
		"Q097B5": {'8': None},
		"Q098A5": {'8': None},
		"Q098B5": {'8': None},
		"Q099A5": {'8': None},
		"Q099B5": {'8': None},
		"Q100A5": {'8': None},
		"Q100B5": {'8': None},
		"Q101A5": {'8': None},
		"Q101B5": {'8': None},
		"Q102A5": {'8': None},
		"Q102B5": {'8': None},


	},
	"ADIR2003": {
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
		"Q30": {'5': None, '9': None},
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
	"ADIR2003_Toddler": {
		"Q011": {'7': None},
		"Q015.1": {'7': None},
		"Q015.2": {'7': None},
		"Q078": {'5': None, '6': None},
		"Q079": {'7': None},
		"Q083": {'7': None},
		"Q083M": {'7': None},
		"Q083F": {'7': None},
		"Q083O": {'7': None},
		"Q085M": {'7': None},
		"Q085F": {'7': None},
		"Q085O": {'7': None},
		"Q086M": {'7': None},
		"Q086F": {'7': None},
		"Q086O": {'7': None},
		"Q100.1": {'7': None},
		"Q100.2": {'7': None},
		"Q103.1": {'7': None},
		"Q103.2": {'7': None},
		"Q108.1": {'7': None},
		"Q108.2": {'7': None},
		"Q113.1": {'7': None},
		"Q113.2": {'7': None},
	},
	"ADOS_Module1": {
	},
	"ADOS_Module2": {
		"QA05": {'8': None},
		"QA06": {'8': None},
	},
	"ADOS_Module3": {
		"QB04": {'-5': None}
	},
	"ADOS_Module4": {},
	"ADOS2_Module1": {
		"QA01": {'8': '4'},
		"QB02": {'8': None},
		"QB07": {'8': None},
		"QB11": {'8': None},
		"QD03": {'3': '2', '8': None}
	},
	"ADOS2_Module2": {
		"QA01": {'7': None},
		"QA04": {'8': None},
		"QA05": {'8': None},
		"QB03": {'8': None},
		"QD03": {'3': '2'}
	},
	"ADOS2_Module3": {
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
	"ADOS2_Module4": {
		"QA02": {'3': '2'},
		'QA03': {'7': None},
		"QB01": {'1': None},
		"QB06": {'3': '2'},
		"QB12": {'8': None},
		"QC01": {'8': None},
	},
	"SRS_Preschool": {
	},
	"SRS_Child": {
	},
	"SRS_Adult": {
	}
}

# These are "missing data" values used in our datasets
instrument_to_missing_data = {
	"ADIR1995": {None, '', ' ', '*', '-1', '-', '990', '991', '992', '993', '994', '995', '996', '997', '998', '999', '9999'},
	"ADIR2003": {None, '', ' ', '*', 'N/A', '-1', '900', '904', '936', '992', '993'},
	"ADIR2003_Toddler": {None, '', ' ', '991', '992', '993', '994', '995', '996', '997', '998', '999'},
	"ADOS_Module1": {None, '', ' ', '-1'},
	"ADOS_Module2": {None, '', ' ', '-1'},
	"ADOS_Module3": {None, '', ' ', '-1'},
	"ADOS_Module4": {None, '', ' ', '-1'},
	"ADOS2_Module1": {None, '', ' ', '-1', '995', '900', '9', '999'},
	"ADOS2_Module2": {None, '', ' ', '-1', '900', '999', '9'},
	"ADOS2_Module3": {None, '', ' ', '-1', '-5', '900', '9', '999'},
	"ADOS2_Module4": {None, '', ' ', '-1', '9'},
	"SRS_Preschool": {None, '-1', '', ' ', '900', '997', '998', '-995'},
	"SRS_Child": {None, '-1', '', ' ', '900', '997', '998', '-995'},
	"SRS_Adult": {None, '-1', '', ' ', '900', '997', '998', '-995'},
}

# These samples have major data issues - for example doubled entries marked as two different genders
bad_samples = {('National Database for Autism Research', 'NDARXR035XHH'),
				('National Database for Autism Research', 'NDARTF820BMV'),
				('AGRE', 'AU2619303')}

# These are aggregated features, scores, and diagnoses that will be filled in by assign_diagnosis.py
instrument_to_scores = {
	"ADIR1995": [],
	"ADIR2003": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior', 'abnormality_evident_before_3_years',
		'A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'],
	"ADIR2003_Toddler": [],
	"ADOS_Module1": [],
	"ADOS_Module2": [],
	"ADOS_Module3": [],
	"ADOS_Module4": [],
	"ADOS2_Module1": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS2_Module2": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS2_Module3": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"ADOS2_Module4": ['diagnosis', 'diagnosis_num_nulls', 'social_interaction', 'communication', 'restricted_repetitive_behavior'],
	"SRS_Preschool": [],
	"SRS_Child": ['diagnosis', 'diagnosis_num_nulls', 'total_raw_score', 'total_t_score', "social_awareness", "social_cognition", "social_communication", "social_motivation", "autistic_mannerisms"],
	"SRS_Adult": [],
	}

def srs_transform(question, value):
	if question in ['Q03', 'Q07', 'Q11', 'Q12', 'Q15', 'Q17', 'Q21', 
					'Q22', 'Q26', 'Q32', 'Q38', 'Q40', 'Q43', 'Q45', 
					'Q48', 'Q52', 'Q55']:
		# Reversed
		return str(4-int(value))
	else:
		return str(int(value)-1)

def adir_short_to_long(m):
	return {
	'Q002': m['Q02'], 'Q004': None, 'Q005': None, 'Q006': None, 'Q007': m['Q04'], 'Q008': m['Q05'], 'Q009': m['Q06'], 'Q010': None, 
	'Q011': m['Q07'], 'Q011E': m['Q07E'], 'Q012': m['Q08'], 'Q013': m['Q09'], 'Q014': m['Q10'], 'Q014E': m['Q10E'], 'Q015': m['Q11'], 'Q015E': m['Q11E'], 'Q016': m['Q15'], 'Q016E': m['Q15E'], 'Q017': m['Q12'], 'Q017E': m['Q12E'], 'Q018': m['Q13'], 'Q018E': m['Q13E'], 'Q019': m['Q14'], 
	'Q020': m['Q16'], 'Q020E': m['Q16E'], 'Q021': None, 'Q021E': None, 'Q022': m['Q17'], 'Q022E': m['Q17E'], 'Q023': m['Q18'], 'Q023E': m['Q18E'], 'Q024': m['Q19'], 'Q024E': m['Q19E'], 'Q025': m['Q20'], 'Q025E': m['Q20E'], 'Q026': None, 'Q026E': None, 'Q027': None, 'Q027E': None, 'Q028': None, 'Q028E': None, 'Q029': m['Q21'], 'Q029E': m['Q21E'], 'Q030': m['Q22'], 'Q030E': m['Q22E'], 
	'Q031': m['Q23'], 'Q031E': m['Q23E'], 'Q032': m['Q24'], 'Q032E': m['Q24E'], 'Q033': m['Q25'], 'Q033E': m['Q25E'], 'Q034': m['Q26'], 'Q034A': m['Q28'], 'Q034AE': m['Q28E'], 'Q034E': m['Q26E'], 'Q035E': m['Q27E'], 'Q036': None, 'Q036E': None, 'Q037E': None, 'Q038E': None, 'Q039E': None, 'Q040E': None, 
	'Q041E': None, 'Q042': m['Q29'], 'Q042E': m['Q29E'], 'Q043': m['Q30'], 'Q043E': m['Q30E'], 'Q044': None, 'Q044E': None, 'Q045': m['Q31'], 'Q045E': m['Q31E'], 'Q046': m['Q32'], 'Q046E': m['Q32E'], 'Q047': m['Q33'], 'Q047E': m['Q33E'], 'Q048': None, 'Q048E': None, 'Q049': m['Q34'], 'Q049E': m['Q34E'], 'Q050': None, 'Q050E': None, 
	'Q051': m['Q35'], 'Q051E': m['Q35E'], 'Q052': m['Q36'], 'Q052E': m['Q36E'], 'Q053': m['Q37'], 'Q053E': m['Q37E'], 'Q054': None, 'Q054E': None, 'Q055': None, 'Q055E': None, 'Q056': None, 'Q056E': None, 'Q057': m['Q38'], 'Q057E': m['Q38E'], 'Q058': None, 'Q058E': None, 'Q059': None, 'Q059E': None, 'Q060': None, 'Q060E': None,
	'Q061': m['Q39'], 'Q061E': m['Q39E'], 'Q062': None, 'Q062E': None, 'Q063': m['Q40'], 'Q063E': m['Q40E'], 'Q064': m['Q41'], 'Q064E': m['Q41E'], 'Q065': m['Q42'], 'Q065E': m['Q42E'], 'Q066': m['Q43'], 'Q066E': m['Q43E'], 'Q067': m['Q44'], 'Q067E': m['Q44E'], 'Q068': m['Q45'], 'Q068E': m['Q45E'], 'Q069': m['Q46'], 'Q069E': m['Q46E'], 'Q070': m['Q47'], 'Q070E': m['Q47E'], 
	'Q071': m['Q48'], 'Q071E': m['Q48E'], 'Q072': m['Q49'], 'Q072E': m['Q49E'], 'Q073': None, 'Q073E': None, 'Q074': None, 'Q074E': None, 'Q075': m['Q50'], 'Q075E': m['Q50E'], 'Q076': None, 'Q076E': None, 'Q077': m['Q51'], 'Q077E': m['Q51E'], 'Q078': None, 'Q078E': None, 'Q079': None, 'Q079E': None, 'Q080': None, 'Q080E': None, 
	'Q081': m['Q52'], 'Q081E': m['Q52E'], 'Q082': None, 'Q082E': None, 'Q083': None, 'Q083E': None, 'Q084': m['Q53'], 'Q084E': m['Q53E'], 'Q085': None, 'Q085E': None, 'Q086': None, 'Q086E': None, 'Q087': None, 'Q088': None, 'Q088E': None, 'Q089': None, 'Q089E': None, 'Q090': m['Q54'], 'Q090E': m['Q54E'], 
	'Q091': None, 'Q091E': None, 'Q091.2': None, 'Q091.2E': None, 'Q091.3': None, 'Q091.3E': None, 'Q092': None, 'Q092E': None, 'Q093': m['Q55'], 'Q094': m['Q56'], 'Q095A5': None, 'Q095B5': None, 'Q096A5': None, 'Q096B5': None, 'Q097A5': None, 'Q097B5': None, 'Q098A5': None, 'Q098B5': None, 'Q099A5': None, 'Q099B5': None, 'Q100A5': None, 'Q100B5': None, 
	'Q101A5': None, 'Q101B5': None, 'Q102A5': None, 'Q102B5': None, 'Q103': None, 'Q104': None, 'Q105': None, 'Q106': m['Q57'], 'Q106E': m['Q57E'], 'Q107': m['Q58'], 'Q107E': m['Q58E'], 'Q108': m['Q59'], 'Q108E': m['Q59E'], 'Q109': m['Q60'], 'Q109E': m['Q60E'], 'Q110': m['Q61'], 'Q110E': m['Q61E'], 'Q111': m['Q62'], 'Q111E': m['Q62E']
	}


# Grab directory
directory = sys.argv[1]

# We'll fill up this dictionary with samples
identifier_to_samples = {}

def update_sample(sample, key, value):
	if sample[key] is None:
		sample[key] = value
	elif key not in ['age', 'interview_date'] and value is not None and sample[key] != value:
		print("%s mismatch" % key, sample['identifier'], sample[key], value)

# This is a very general method that converts csv data to json given a mapping
def convert_phenotypes(filename, dataset, instrument, lambdas, cols, 
	num_headers=1, delimiter=',', value_transform=None):
	print("Importing %s" % filename)

	with open("%s/%s" % (directory, filename), encoding='utf-8', errors='ignore') as f:
		reader = csv.reader(f, delimiter=delimiter)

		# Skip header
		for _ in range(num_headers):
			next(reader)

		for pieces in reader:
			identifier = lambdas["identifier"](pieces)

			# Determine whether or not we've already seen this sample
			if (dataset, identifier) in identifier_to_samples:
				sample = identifier_to_samples[(dataset, identifier)]

				# Update sample with new information, if it exists
				for key, value in lambdas.items():
					update_sample(sample, key, value(pieces))
			else:
				# Create new sample
				sample = {
					"dataset": dataset,
					"diagnosis": None,
					"clinical_diagnosis": None,
					"cpea_diagnosis": None,
					"cpea_adjusted_diagnosis": None
				}
				for key, value in lambdas.items():
					sample[key] = value(pieces)
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

						# Trasnform answer
						if value_transform is not None and answer not in missing_data:
							answer = value_transform(q_num, answer)

						# Transform answer in the case of an exception
						if q_num in exceptions:
							q_except = exceptions[q_num]
							if answer in q_except:
								answer = q_except[answer]

						# Grab set of code values from table
						coded_values = codes[q_num]

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

# # # ***************************************************************************************************************
# # # *
# # # --------------------------------------------------- AGRE ------------------------------------------------------
# # # *
# # # ***************************************************************************************************************

# # Pull diagnosis
# agre_diagnosis = {}
# with open(directory + "/AGRE_2015/AGRE Pedigree Catalog 10-05-12/AGRE Pedigree Catalog 10-05-2012.csv", 'r', encoding = "ISO-8859-1") as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	agre_diagnosis.update([(x[2], x[11]) for x in reader])

# with open(directory + "/AGRE_2010/AGREpedigreesR_102007.csv", 'r', encoding = "ISO-8859-1") as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	agre_diagnosis.update([(x[2], x[10]) for x in reader])

# ped_map = {'0': None, '-9': None, '1': 'unaffected', '2': 'affected'}
# with open(directory + '/160826.ped', 'r') as f:
# 	reader = csv.reader(f, delimiter='\t')
# 	for line in reader:
# 		if line[5] != '' and line[1] not in agre_diagnosis:
# 			agre_diagnosis[line[1]] = ped_map[line[5]]

# # ADIR1995
# map1995 = {
# 	'Q002': 20, 'Q004': 218, 'Q005': 23, 'Q006': 220, 'Q007': 24, 'Q008': 222, 'Q009': 223, 'Q010': 28, 
# 	'Q011': 73, 'Q011E': 74, 'Q012': 30, 'Q013': 32, 'Q014': 75, 'Q014E': 76, 'Q015': 224, 'Q015E': 225, 'Q016': 79, 'Q016E': 80, 'Q017': 227, 'Q017E': 228, 'Q018': 77, 'Q018E': 78, 'Q019': 72, 
# 	'Q020': 81, 'Q020E': 82, 'Q021': 229, 'Q021E': 230, 'Q022': 83, 'Q022E': 84, 'Q023': 86, 'Q023E': 87, 'Q024': 89, 'Q024E': 90, 'Q025': 92, 'Q025E': 93, 'Q026': 95, 'Q026E': 96, 'Q027': 231, 'Q027E': 232, 'Q028': 98, 'Q028E': 99, 'Q029': 114, 'Q029E': 115, 'Q030': 101, 'Q030E': 102, 
# 	'Q031': 109, 'Q031E': 110, 'Q032': 103, 'Q032E': 104, 'Q033': 106, 'Q033E': 107, 'Q034': 111, 'Q034A': 70, 'Q034AE': 71, 'Q034E': 112, 'Q035E': 234, 'Q036': 168, 'Q036E': 169, 'Q037E': 36, 'Q038E': 38, 'Q039E': 40, 'Q040E': 42, 
# 	'Q041E': 44, 'Q042': 121, 'Q042E': 122, 'Q043': 123, 'Q043E': 124, 'Q044': 235, 'Q044E': 236, 'Q045': 125, 'Q045E': 126, 'Q046': 127, 'Q046E': 128, 'Q047': 129, 'Q047E': 130, 'Q048': 238, 'Q048E': 239, 'Q049': 131, 'Q049E': 132, 'Q050': 240, 'Q050E': 241, 
# 	'Q051': 133, 'Q051E': 134, 'Q052': 135, 'Q052E': 136, 'Q053': 138, 'Q053E': 139, 'Q054': 244, 'Q054E': 245, 'Q055': 246, 'Q055E': 247, 'Q056': 156, 'Q056E': 157, 'Q057': 141, 'Q057E': 142, 'Q058': 248, 'Q058E': 249, 'Q059': 250, 'Q059E': 251, 'Q060': 252, 'Q060E': 253,
# 	'Q061': 144, 'Q061E': 145, 'Q062': 255, 'Q062E': 256, 'Q063': 117, 'Q063E': 118, 'Q064': 119, 'Q064E': 120, 'Q065': 146, 'Q065E': 147, 'Q066': 148, 'Q066E': 149, 'Q067': 150, 'Q067E': 151, 'Q068': 152, 'Q068E': 153, 'Q069': 154, 'Q069E': 155, 'Q070': 160, 'Q070E': 161, 
# 	'Q071': 158, 'Q071E': 159, 'Q072': 162, 'Q072E': 163, 'Q073': 172, 'Q073E': 173, 'Q074': 174, 'Q074E': 175, 'Q075': 164, 'Q075E': 165, 'Q076': 176, 'Q076E': 177, 'Q077': 166, 'Q077E': 167, 'Q078': 170, 'Q078E': 171, 'Q079': 257, 'Q079E': 258, 'Q080': 192, 'Q080E': 193, 
# 	'Q081': 178, 'Q081E': 179, 'Q082': 182, 'Q082E': 183, 'Q083': 259, 'Q083E': 260, 'Q084': 180, 'Q084E': 181, 'Q085': 261, 'Q085E': 262, 'Q086': 184, 'Q086E': 185, 'Q087': 263, 'Q088': 264, 'Q088E': 265, 'Q089': 266, 'Q089E': 267, 'Q090': 190, 'Q090E': 191, 
# 	'Q091': 268, 'Q091E': 269, 'Q091.2': 186, 'Q091.2E': 187, 'Q091.3': 188, 'Q091.3E': 189, 'Q092': 194, 'Q092E': 195, 'Q093': 196, 'Q094': 197, 'Q095A5': 270, 'Q095B5': 271, 'Q096A5': 273, 'Q096B5': 272, 'Q097A5': 275, 'Q097B5': 274, 'Q098A5': 277, 'Q098B5': 276, 'Q099A5': 279, 'Q099B5': 278, 'Q100A5': 281, 'Q100B5': 280, 
# 	'Q101A5': 283, 'Q101B5': 282, 'Q102A5': 285, 'Q102B5': 284, 'Q103': 64, 'Q104': 286, 'Q105': 68, 'Q106': 287, 'Q106E': 288, 'Q107': 289, 'Q107E': 290, 'Q108': 291, 'Q108E': 292, 'Q109': 293, 'Q109E': 294, 'Q110': 295, 'Q110E': 296, 'Q111': 297, 'Q111E': 298
# 	}
# convert_phenotypes("AGRE_2010/ADIR/ADIR_combined1995.csv", "AGRE", "ADIR1995",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	map1995)

# # ADIR1995
# convert_phenotypes("AGRE_2015/ADIR/ADIR_combined1995.csv", "AGRE", "ADIR1995",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict([(k, v+4 if v <= 220 else v+3 if v <= 242 else v+2) for k, v in map1995.items()]))


# # ADIR2003
# map2003 = {
# 		"Q02": 20, "Q04": 23, "Q05": 24, "Q06": 26, "Q07": 27, "Q08": 28, "Q09": 30, "Q10": 32,
# 		"Q11": 34, "Q12": 36, "Q13": 38, "Q14": 40, "Q15": 42, "Q16": 44, "Q17": 46, "Q18": 48, "Q19": 50, "Q20": 52,
# 		"Q21": 54, "Q22": 56, "Q23": 58, "Q24": 60, "Q25": 62, "Q26": 64, "Q27": 66, "Q28": 68, "Q29.1": 70, "Q29.2": 71, "Q30": 72,
# 		"Q31.1": 73, "Q31.2": 74, "Q32.1": 75, "Q32.2": 76, "Q33.1": 77, "Q33.2": 78, "Q34.1": 79, "Q34.2": 80, "Q35.1": 81, "Q35.2": 82, "Q36.1": 83, "Q36.2": 84, "Q37.1": 86, "Q37.2": 87, "Q38.1": 89, "Q38.2": 90, "Q39.1": 92, "Q39.2": 93, "Q40.1": 95, "Q40.2": 96,
# 		"Q41.1": 98, "Q41.2": 99, "Q42.1": 101, "Q42.2": 102, "Q43.1": 103, "Q43.2": 104, "Q44.1": 106, "Q44.2": 107, "Q45.1": 109, "Q45.2": 110, "Q46.1": 111, "Q46.2": 112, "Q47.1": 114, "Q47.2": 115, "Q48.1": 117, "Q48.2": 118, "Q49.1": 119, "Q49.2": 120, "Q50.1": 121, "Q50.2": 122,
# 		"Q51.1": 123, "Q51.2": 124, "Q52.1": 125, "Q52.2": 126, "Q53.1": 127, "Q53.2": 128, "Q54.1": 129, "Q54.2": 130, "Q55.1": 131, "Q55.2": 132, "Q56.1": 133, "Q56.2": 134, "Q57.1": 135, "Q57.2": 136, "Q58.1": 138, "Q58.2": 139, "Q59.1": 141, "Q59.2": 142, "Q60.1": 144, "Q60.2": 145,
# 		"Q61.1": 146, "Q61.2": 147, "Q62.1": 148, "Q62.2": 149, "Q63.1": 150, "Q63.2": 151, "Q64.1": 152, "Q64.2": 153, "Q65.1": 154, "Q65.2": 155, "Q66.1": 156, "Q66.2": 157, "Q67.1": 158, "Q67.2": 159, "Q68.1": 160, "Q68.2": 161, "Q69.1": 162, "Q69.2": 163, "Q70.1": 164, "Q70.2": 165,
# 		"Q71.1": 166, "Q71.2": 167, "Q72.1": 168, "Q72.2": 169, "Q73.1": 170, "Q73.2": 171, "Q74.1": 172, "Q74.2": 173, "Q75.1": 174, "Q75.2": 175, "Q76.1": 176, "Q76.2": 177, "Q77.1": 178, "Q77.2": 179, "Q78.1": 180, "Q78.2": 181, "Q79.1": 182, "Q79.2": 183, "Q80.1": 184, "Q80.2": 185,
# 		"Q81.1": 186, "Q81.2": 187, "Q82.1": 188, "Q82.2": 189, "Q83.1": 190, "Q83.2": 191, "Q84.1": 192, "Q84.2": 193, "Q85.1": 194, "Q85.2": 195, "Q86": 196, "Q87": 197, "Q88.1": 198, "Q88.2": 199, "Q89.1": 200, "Q89.2": 201, "Q90.1": 202, "Q90.2": 203,
# 		"Q91.1": 204, "Q91.2": 205, "Q92.1": 206, "Q92.2": 207, "Q93.1": 208, "Q93.2": 209
# 	}
# convert_phenotypes("AGRE_2010/ADIR/ADIR_combined2003.csv", "AGRE", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	map2003)

# # ADIR2003
# convert_phenotypes("AGRE_2015/ADIR/ADIR_combined2003.csv", "AGRE", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict([(k, v+4) for k, v in map2003.items()]))

# # ADOS_Module1
# convert_phenotypes("AGRE_2015/ADOS Mod1/ADOS_combined.csv", "AGRE", "ADOS_Module1",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, 
# 		"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": 37, "QB11": 38, "QB12": 39,
# 		"QC01": 45, "QC02": 46, 
# 		"QD01": 47, "QD02": 48, "QD03": 49, "QD04": 50, 
# 		"QE01": 51, "QE02": 52, "QE03": 53
# 	})

# # ADOS2_Module1
# convert_phenotypes("AGRE_2015/ADOS Mod1/ADOS2_combined.csv", "AGRE", "ADOS2_Module1",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, 
# 		"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": 37, "QB11": 38, "QB12": 39, "QB13.1": 40, "QB13.2": 41, "QB14": 42, "QB15": 43, "QB16": 44,
# 		"QC01": 45, "QC02": 46, 
# 		"QD01": 47, "QD02": 48, "QD03": 49, "QD04": 50, 
# 		"QE01": 51, "QE02": 52, "QE03": 53
# 	})

# # ADOS_Module1
# convert_phenotypes("AGRE_2010/ADOS Module 1/ADOS11.csv", "AGRE", "ADOS_Module1",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 47, "QA02": 48, "QA03": 49, "QA04": 50, "QA05": 51, "QA06": 52, "QA07": 53, "QA08": 54, 
# 		"QB01": 55, "QB02": 56, "QB03": 57, "QB04": 58, "QB05": 59, "QB06": 60, "QB07": 61, "QB08": 62, "QB09": 63, "QB10": 64, "QB11": 65, "QB12": 66,
# 		"QC01": 67, "QC02": 68, 
# 		"QD01": 69, "QD02": 70, "QD03": 71, "QD04": 72, 
# 		"QE01": 73, "QE02": 74, "QE03": 75
# 	})

# # ADOS_Module2
# convert_phenotypes("AGRE_2015/ADOS Mod2/ADOS_combined.csv", "AGRE", "ADOS_Module2",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 35, "QA03": 21, "QA04": 22, "QA05": 23, "QA06": 24, "QA07": 30, 'QA08': 25, 'QA09': 26, 
# 		"QB01": 27, "QB02": 28, "QB03": 29, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 37, "QB09": 35, "QB10": 39,
# 		"QC01": 40, "QC02": 41, 
# 		"QD01": 42, "QD02": 43, "QD03": 44, "QD04": 45, 
# 		"QE01": 46, "QE02": 47, "QE03": 48
# 	})

# # ADOS_Module2
# convert_phenotypes("AGRE_2015/ADOS Mod2/ADOS2_combined.csv", "AGRE", "ADOS2_Module2",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, 
# 		"QB01": 27, "QB02": 28, "QB03": 29, "QB04": 30, "QB05": 31, "QB06": 32, "QB07": 33, "QB08": 34, "QB09.1": 35, "QB09.2": 36, "QB10": 37, "QB11": 38, "QB12": 39,
# 		"QC01": 40, "QC02": 41, 
# 		"QD01": 42, "QD02": 43, "QD03": 44, "QD04": 45, 
# 		"QE01": 46, "QE02": 47, "QE03": 48
# 	})

# # ADOS_Module2
# convert_phenotypes("AGRE_2010/ADOS Module 2/ADOS21.csv", "AGRE", "ADOS_Module2",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	},  
# 	{
# 		"QA01": 46, "QA02": 47, "QA03": 48, "QA04": 49, "QA05": 50, "QA06": 51, "QA07": 57, 'QA08': 52, 'QA09': 53, 
# 		"QB01": 54, "QB02": 55, "QB03": 56, "QB04": 58, "QB05": 59, "QB06": 60, "QB07": 61, "QB08": 62, "QB09": 63, "QB10": 64,
# 		"QC01": 65, "QC02": 66, 
# 		"QD01": 67, "QD02": 68, "QD03": 69, "QD04": 70, 
# 		"QE01": 71, "QE02": 72, "QE03": 73
# 	})

# # ADOS_Module3
# convert_phenotypes("AGRE_2015/ADOS Mod3/ADOS_combined.csv", "AGRE", "ADOS_Module3",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, "QA09": 28, 
# 		"QB01": 29, "QB02": 30, "QB03": 31, "QB04": 32, "QB05": 33, "QB06": 34, "QB07": 35, "QB08": 37, "QB09": 39, "QB10": 39,
# 		"QC01": 40,
# 		"QD01": 41, "QD02": 42, "QD03": 43, "QD04": 44, "QD05": 45,
# 		"QE01": 46, "QE02": 47, "QE03": 48
# 	})

# convert_phenotypes("AGRE_2015/ADOS Mod3/ADOS2_combined.csv", "AGRE", "ADOS2_Module3",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
# 		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, "QA09": 28, 
# 		"QB01": 29, "QB02": 30, "QB03": 31, "QB04": 32, "QB05": 33, "QB06": 34, "QB07": 35, "QB08": 36, "QB09": 37, "QB10": 38, "QB11": 39,
# 		"QC01": 40,
# 		"QD01": 41, "QD02": 42, "QD03": 43, "QD04": 44, "QD05": 45,
# 		"QE01": 46, "QE02": 47, "QE03": 48
# 	})

# # ADOS3
# convert_phenotypes("AGRE_2010/ADOS Module 3/ADOS31.csv", "AGRE", "ADOS_Module3",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	},  
# 	{
#  		"QA01": 46, "QA02": 47, "QA03": 48, "QA04": 49, "QA05": 50, "QA06": 51, "QA07": 52, "QA08": 53, "QA09": 54, 
#  		"QB01": 55, "QB02": 56, "QB03": 57, "QB04": 58, "QB05": 59, "QB06": 60, "QB07": 61, "QB08": 62, "QB09": 63, "QB10": 64,
#  		"QC01": 65,
#  		"QD01": 66, "QD02": 67, "QD03": 68, "QD04": 69, "QD05": 70,
#  		"QE01": 71, "QE02": 72, "QE03": 73
#  	})

# # ADOS_Module4
# convert_phenotypes("AGRE_2015/ADOS Mod4/ADOS41.csv", "AGRE", "ADOS_Module4",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	{
#  		"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, "QA09": 28, "QA10": 29, 
#  		"QB01": 30, "QB02": 31, "QB03": 32, "QB04": 34, "QB05": 35, "QB06": 36, "QB07": 37, "QB08": 38, "QB09": 40, "QB10": 41, "QB11": 42,
#  		"QC01": 43, 
#  		"QD01": 44, "QD02": 45, "QD03": 46, "QD04": 47, "QD05": 48,
#  		"QE01": 49, "QE02": 50, "QE03": 51
#  	})

# # ADOS_Module4
# convert_phenotypes("AGRE_2010/ADOS Module 4/ADOS41.csv", "AGRE", "ADOS_Module4",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	},  
# 	{
# 		"QA01": 49, "QA02": 50, "QA03": 51, "QA04": 52, "QA05": 53, "QA06": 54, "QA07": 55, "QA08": 56, "QA09": 57, "QA10": 58, 
# 		"QB01": 59, "QB02": 60, "QB03": 61, "QB04": 63, "QB05": 64, "QB06": 65, "QB07": 66, "QB08": 67, "QB09": 68, "QB10": 69, "QB11": 70,
# 		"QC01": 71, 
# 		"QD01": 72, "QD02": 73, "QD03": 74, "QD04": 75, "QD05": 76,
# 		"QE01": 77, "QE02": 78, "QE03": 79
# 	})

# # SRS
# convert_phenotypes("AGRE_2010/SRS Child/SRS_Child1.csv", "AGRE", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[12]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[9], x[10], x[11]),
# 		"family": lambda x: x[7],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(20, 85))))

# # SRS_Preschool
# convert_phenotypes("AGRE_2015/SRS/SRS_2006_Preschool1.csv", "AGRE", "SRS_Preschool",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(24, 89))))

# # SRS_Child
# convert_phenotypes("AGRE_2015/SRS/SRS_20061_Child.csv", "AGRE", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(24, 89))), 
# 	value_transform=srs_transform)

# # SRS_Adult
# convert_phenotypes("AGRE_2015/SRS/SRS_20061_Adult.csv", "AGRE", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(24, 89))), 
# 	value_transform=srs_transform)

# convert_phenotypes("AGRE_2015/SRS/SRS2_SRS20021_Preschool.csv", "AGRE", "SRS_Preschool",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(24, 89))))

# convert_phenotypes("AGRE_2015/SRS/SRS2_SRS20021_Child.csv", "AGRE", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[6],
# 		"gender": lambda x: "Male" if x[5] == "1" else ("Female" if x[5] == "2" else None),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(round(12*float(x[16]), 0)),
# 		"interview_date": lambda x: "%s/%s/%s" % (x[13], x[14], x[15]),
# 		"family": lambda x: x[10],
# 		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(24, 89))))

# # Medical History
# print("Importing %s" % "%s/%s" % (directory, "AGRE_2015/secondary_diagnoses.txt"))

# # Import diagnosis categories
# diagnosis_to_category = dict()
# with open("%s/%s" % (directory, "AGRE_2015/secondary_diagnoses_categories.txt")) as f:
# 	for line in f:
# 		pieces = line.strip().split("\t")
# 		diagnosis_to_category[pieces[0].lower()] = pieces[1]

# # Pull medical histories and insert them into schema
# not_found = set()
# with open("%s/%s" % (directory, "AGRE_2015/secondary_diagnoses.txt")) as f:
# 	next(f)
# 	for line in f:
# 		pieces = line.split("\t")
# 		if ("AGRE", pieces[0]) in identifier_to_samples:
# 			sample = identifier_to_samples[("AGRE", pieces[0])]
# 			sample["Medical History"] = {
# 				"ID": 0,
# 				"Seizures": 0,
# 				"Tourette or Tic Disorder": 0,
# 				"Mood Disorder": 0,
# 				"Anxiety Disorder": 0,
# 				"Psychotic Disorder": 0,
# 				"Autoimmune/Allergic": 0,
# 				"Behavior": 0,
# 			}
# 			for secondary_diagnosis in pieces[1].strip().lower().split('; '):
# 				if secondary_diagnosis in diagnosis_to_category:
# 					sample["Medical History"][diagnosis_to_category[secondary_diagnosis]] = 1
# 				else:
# 					not_found.add(secondary_diagnosis)

# print("Secondary diagnoses not found:", sorted(not_found))

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- AC ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# # Pull diagnosis
# ac_diagnosis = {}
# with open(directory + "/Autism_Consortium_Data/All_Measures/AC_Medical_History.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	for x in reader:
# 		if x[645] == '2':
# 			ac_diagnosis[x[0]] = 'autism'
# 		elif x[660] == '2':
# 			ac_diagnosis[x[0]] = 'aspergers'
# 		elif x[675] == '2':
# 			ac_diagnosis[x[0]] = 'PDD-NOS'

# # ADIR2003
# convert_phenotypes("Autism_Consortium_Data/All_Measures/ADI_R.csv", "Autism Consortium", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	}, 
# 	{
# 		"Q02": (36, 37), "Q04": 39, "Q05": (40, 41), "Q06": (42, 43), "Q07": (44, 45), "Q08": (46, 47), "Q09": (48, 49), "Q10": (50, 51),
# 		"Q11": 52, "Q12": 53, "Q13": 54, "Q14": 55, "Q15": 56, "Q16": 57, "Q17": (58, 59), "Q18": 60, "Q19": (62, 63), "Q20": 64,
# 		"Q21": 65, "Q22": 66, "Q23": 67, "Q24": 68, "Q25": 69, "Q26": (70, 71), "Q27": 72, "Q28": (74, 75), "Q29.1": 76, "Q29.2": 77, "Q30": 78,
# 		"Q31.1": 79, "Q31.2": 80, "Q32.1": 81, "Q32.2": 82, "Q33.1": 83, "Q33.2": 84, "Q34.1": 85, "Q34.2": 86, "Q35.1": 87, "Q35.2": 88, "Q36.1": 89, "Q36.2": 90, "Q37.1": 91, "Q37.2": 92, "Q38.1": 93, "Q38.2": 94, "Q39.1": 95, "Q39.2": 96, "Q40.1": 97, "Q40.2": 98,
# 		"Q41.1": 99, "Q41.2": 100, "Q42.1": 101, "Q42.2": 102, "Q43.1": 103, "Q43.2": 104, "Q44.1": 105, "Q44.2": 106, "Q45.1": 107, "Q45.2": 108, "Q46.1": 109, "Q46.2": 110, "Q47.1": 111, "Q47.2": 112, "Q48.1": 113, "Q48.2": 114, "Q49.1": 115, "Q49.2": 116, "Q50.1": 117, "Q50.2": 118,
# 		"Q51.1": 119, "Q51.2": 120, "Q52.1": 121, "Q52.2": 122, "Q53.1": 123, "Q53.2": 124, "Q54.1": 125, "Q54.2": 126, "Q55.1": 127, "Q55.2": 128, "Q56.1": 129, "Q56.2": 130, "Q57.1": 131, "Q57.2": 132, "Q58.1": 134, "Q58.2": 135, "Q59.1": 136, "Q59.2": 137, "Q60.1": 140, "Q60.2": 141,
# 		"Q61.1": 142, "Q61.2": 143, "Q62.1": 144, "Q62.2": 145, "Q63.1": 146, "Q63.2": 147, "Q64.1": 148, "Q64.2": 149, "Q65.1": 150, "Q65.2": 151, "Q66.1": 152, "Q66.2": 153, "Q67.1": 154, "Q67.2": 155, "Q68.1": 156, "Q68.2": 157, "Q69.1": 158, "Q69.2": 159, "Q70.1": 160, "Q70.2": 161,
# 		"Q71.1": 162, "Q71.2": 163, "Q72.1": 164, "Q72.2": 165, "Q73.1": 166, "Q73.2": 167, "Q74.1": 168, "Q74.2": 169, "Q75.1": 170, "Q75.2": 171, "Q76.1": 172, "Q76.2": 173, "Q77.1": 175, "Q77.2": 175, "Q78.1": 176, "Q78.2": 177, "Q79.1": 178, "Q79.2": 179, "Q80.1": 180, "Q80.2": 181,
# 		"Q81.1": 182, "Q81.2": 183, "Q82.1": 184, "Q82.2": 185, "Q83.1": 186, "Q83.2": 187, "Q84.1": 188, "Q84.2": 189, "Q85.1": 190, "Q85.2": 191, "Q86": 192, "Q87": 193, "Q88.1": 194, "Q88.2": 195, "Q89.1": 196, "Q89.2": 197, "Q90.1": 198, "Q90.2": 199,
# 		"Q91.1": 200, "Q91.2": 201, "Q92.1": 202, "Q92.2": 203, "Q93.1": 204, "Q93.2": 205
# 	})

# # ADOS1
# convert_phenotypes("Autism_Consortium_Data/All_Measures/ADOS_Module_1.csv", "Autism Consortium", "ADOS_Module1",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, 
# 		"QB01": 19, "QB02": 20, "QB03": 21, "QB04": 22, "QB05": 23, "QB06": 24, "QB07": 25, "QB08": 26, "QB09": 27, "QB10": 28, "QB11": 29, "QB12": 30, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 		"QC01": 31, "QC02": 32, 
# 		"QD01": 33, "QD02": 35, "QD03": 37, "QD04": 38, 
# 		"QE01": 40, "QE02": 41, "QE03": 42
# 	})

# # ADOS2
# convert_phenotypes("Autism_Consortium_Data/All_Measures/ADOS_Module_2.csv", "Autism Consortium", "ADOS_Module2",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 11, "QA02": 13, "QA03": 14, "QA04": 15, "QA05": 16, "QA06": 17, "QA07": 18, 
# 		"QB01": 19, "QB02": 20, "QB03": 21, "QB04": 22, "QB05": 23, "QB06": 24, "QB07": 25, "QB08": 26, "QB09.1": None, "QB09.2": None, "QB10": 27, "QB11": 28, "QB12": 29,
# 		"QC01": 30, "QC02": 31, 
# 		"QD01": 32, "QD02": 34, "QD03": 36, "QD04": 37, 
# 		"QE01": 39, "QE02": 40, "QE03": 41
# 	})

# # ADOS3
# convert_phenotypes("Autism_Consortium_Data/All_Measures/ADOS_Module_3.csv", "Autism Consortium", "ADOS_Module3",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, "QA09": 19, 
# 		"QB01": 20, "QB02": 21, "QB03": 22, "QB04": 23, "QB05": 24, "QB06": 25, "QB07": 26, "QB08": None, "QB09": 27, "QB10": 28, "QB11": 29,
# 		"QC01": 30,
# 		"QD01": 31, "QD02": 33, "QD03": 35, "QD04": 36, "QD05": 37, 
# 		"QE01": 39, "QE02": 40, "QE03": 41
# 	})

# # ADOS4
# convert_phenotypes("Autism_Consortium_Data/All_Measures/ADOS_Module_4.csv", "Autism Consortium", "ADOS_Module4",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 11, "QA02": 12, "QA03": 13, "QA04": 14, "QA05": 15, "QA06": 16, "QA07": 17, "QA08": 18, "QA09": 19, "QA10": 20, 
# 		"QB01": 21, "QB02": 22, "QB03": 23, "QB04": 24, "QB05": 25, "QB06": 26, "QB07": 27, "QB08": 28, "QB09": 29, "QB10": None, "QB11": 30, "QB12": 31, "QB13": 32,
# 		"QC01": 33,
# 		"QD01": 34, "QD02": 36, "QD03": 38, "QD04": 39, "QD05": 40, 
# 		"QE01": 42, "QE02": 45, "QE03": 44
# 	})

# # SRS
# convert_phenotypes("Autism_Consortium_Data/All_Measures/SRS_Preschool.csv", "Autism Consortium", "SRS_Preschool",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(76, 141))))

# convert_phenotypes("Autism_Consortium_Data/All_Measures/SRS_Parent.csv", "Autism Consortium", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(76, 141))))

# convert_phenotypes("Autism_Consortium_Data/All_Measures/SRS_Adult.csv", "Autism Consortium", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: "Male" if x[1] == "M" else ("Female" if x[1] == "F" else None),
# 		"race": lambda x: x[2],
# 		"ethnicity": lambda x: x[3],
# 		"age": lambda x: int(round(float(x[8]), 0)),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: x[0][0:x[0].rfind("-")],
# 		"clinical_diagnosis_raw": lambda x: x[6] if x[0] not in ac_diagnosis else ac_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(76, 141))))

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- NDAR ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# path = "ndar.phenotype.collection"
# for filename in os.listdir("%s/%s" % (directory, path)):
# 	subpath = os.path.join(path, filename)

# 	if os.path.isdir("%s/%s" % (directory, subpath)) and 'AGRE' not in subpath:

# 		# Pull diagnosis
# 		ndar_diagnosis = {}
# 		try:
# 			with open('%s/%s/ndar_aggregate.txt' % (directory, subpath), 'r') as f:
# 				reader = csv.reader(f, delimiter='\t')
# 				header = next(reader)[1:]
# 				ndar_diagnosis = dict([(x[0], x[4] if x[4] != '' else x[3]) for x in reader])
# 		except:
# 			print('Diagnosis file not found', '%s/%s/ndar_aggregate.txt' % (directory, subpath))

# 		# Assign diagnosis to alternate ids
# 		id_to_id = {}
# 		try:
# 			with open('%s/%s/guid_parent_child.txt' % (directory, subpath), 'r') as f:
# 				reader = csv.reader(f, delimiter='\t')
# 				header = next(reader)[1:]
# 				for parent, child in reader:
# 					if parent in ndar_diagnosis:
# 						ndar_diagnosis[child] = ndar_diagnosis[parent]
# 					elif child in ndar_diagnosis:
# 						ndar_diagnosis[parent] = ndar_diagnosis[child]
# 					id_to_id[child] = parent
# 		except:
# 			pass
# 			#print('Id file not found', '%s/%s/guid_parent_child.txt' % (directory, subpath))

# 		identifier_lambda = lambda x: x[2] if x[2] not in id_to_id else id_to_id[x[2]]
# 		clinical_diagnosis_lambda = lambda x: None if x[2] not in ndar_diagnosis else ndar_diagnosis[x[2]]
		
		# # ADIR2003
		# filename = os.path.join(subpath, "adi_200304.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", 'ADIR2003', 
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[22] == "M" else ("Female" if x[22] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: int(round(float(x[3]), 0)),
		# 			"interview_date": lambda x: x[5],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		},
		# 		{
		# 			"Q02": 26, "Q04": 28, "Q05": 31, "Q06": 33, "Q07": 34, "Q08": 35, "Q09": 37, "Q10": 41,
		# 			"Q11": 43, "Q12": 44, "Q13": 45, "Q14": 46, "Q15": 47, "Q16": 48, "Q17": 49, "Q18": 50, "Q19": 53, "Q20": 54,
		# 			"Q21": 55, "Q22": 56, "Q23": 57, "Q24": 58, "Q25": 59, "Q26": 61, "Q27": 62, "Q28": 63, "Q29.1": 64, "Q29.2": 65, "Q30": 67,
		# 			"Q31.1": 68, "Q31.2": 69, "Q32.1": 70, "Q32.2": 71, "Q33.1": 72, "Q33.2": 73, "Q34.1": 74, "Q34.2": 75, "Q35.1": 76, "Q35.2": 77, "Q36.1": 78, "Q36.2": 79, "Q37.1": 81, "Q37.2": 82, "Q38.1": 84, "Q38.2": 85, "Q39.1": 87, "Q39.2": 88, "Q40.1": 91, "Q40.2": 92,
		# 			"Q41.1": 94, "Q41.2": 95, "Q42.1": 97, "Q42.2": 98, "Q43.1": 99, "Q43.2": 100, "Q44.1": 102, "Q44.2": 103, "Q45.1": 105, "Q45.2": 106, "Q46.1": 107, "Q46.2": 108, "Q47.1": 110, "Q47.2": 111, "Q48.1": 113, "Q48.2": 114, "Q49.1": 116, "Q49.2": 117, "Q50.1": 118, "Q50.2": 119,
		# 			"Q51.1": 120, "Q51.2": 121, "Q52.1": 122, "Q52.2": 123, "Q53.1": 124, "Q53.2": 125, "Q54.1": 126, "Q54.2": 127, "Q55.1": 128, "Q55.2": 129, "Q56.1": 130, "Q56.2": 131, "Q57.1": 133, "Q57.2": 134, "Q58.1": 136, "Q58.2": 137, "Q59.1": 139, "Q59.2": 140, "Q60.1": 154, "Q60.2": 155,
		# 			"Q61.1": 157, "Q61.2": 158, "Q62.1": 159, "Q62.2": 160, "Q63.1": 161, "Q63.2": 162, "Q64.1": 163, "Q64.2": 164, "Q65.1": 165, "Q65.2": 166, "Q66.1": 168, "Q66.2": 169, "Q67.1": 171, "Q67.2": 172, "Q68.1": 173, "Q68.2": 174, "Q69.1": 176, "Q69.2": 177, "Q70.1": 178, "Q70.2": 179,
		# 			"Q71.1": 181, "Q71.2": 182, "Q72.1": 184, "Q72.2": 185, "Q73.1": 186, "Q73.2": 187, "Q74.1": 189, "Q74.2": 190, "Q75.1": 192, "Q75.2": 193, "Q76.1": 195, "Q76.2": 196, "Q77.1": 198, "Q77.2": 199, "Q78.1": 201, "Q78.2": 202, "Q79.1": 204, "Q79.2": 205, "Q80.1": 206, "Q80.2": 207,
		# 			"Q81.1": 209, "Q81.2": 210, "Q82.1": 212, "Q82.2": 213, "Q83.1": 215, "Q83.2": 216, "Q84.1": 218, "Q84.2": 219, "Q85.1": 220, "Q85.2": 221, "Q86": 223, "Q87": 224, "Q88.1": 225, "Q88.2": 226, "Q89.1": 227, "Q89.2": 228, "Q90.1": 229, "Q90.2": 230,
		# 			"Q91.1": 231, "Q91.2": 232, "Q92.1": 233, "Q92.2": 234, "Q93.1": 235, "Q93.2": 236
		# 		}, num_headers=2, delimiter='\t')

		# # ADIR2003
		# filename = os.path.join(subpath, "adi_c02.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", "ADIR2003", 
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: None if x[5] == '' else int(round(float(x[5]), 0)),
		# 			"interview_date": lambda x: x[4],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		}, 
		# 		{
		# 			"Q02": 13, "Q04": 12, "Q05": 14, "Q06": 15, "Q07": 16, "Q08": 17, "Q09": 18, "Q10": 19,
		# 			"Q11": 20, "Q12": 21, "Q13": 22, "Q14": 23, "Q15": 24, "Q16": 25, "Q17": 26, "Q18": 27, "Q19": 28, "Q20": 29,
		# 			"Q21": 30, "Q22": 31, "Q23": 32, "Q24": 33, "Q25": None, "Q26": 34, "Q27": 35, "Q28": None, "Q29.1": 36, "Q29.2": 37, "Q30": 38,
		# 			"Q31.1": 39, "Q31.2": 40, "Q32.1": 41, "Q32.2": 42, "Q33.1": 43, "Q33.2": 44, "Q34.1": 45, "Q34.2": None, "Q35.1": None, "Q35.2": None, "Q36.1": 46, "Q36.2": 47, "Q37.1": 48, "Q37.2": 49, "Q38.1": 50, "Q38.2": 51, "Q39.1": 52, "Q39.2": 53, "Q40.1": 54, "Q40.2": 55,
		# 			"Q41.1": 56, "Q41.2": 57, "Q42.1": 58, "Q42.2": 59, "Q43.1": 60, "Q43.2": 61, "Q44.1": 62, "Q44.2": 63, "Q45.1": 64, "Q45.2": 65, "Q46.1": 66, "Q46.2": 67, "Q47.1": 68, "Q47.2": 69, "Q48.1": 70, "Q48.2": 71, "Q49.1": 72, "Q49.2": 73, "Q50.1": 74, "Q50.2": 75,
		# 			"Q51.1": 76, "Q51.2": 77, "Q52.1": 78, "Q52.2": 79, "Q53.1": 80, "Q53.2": 81, "Q54.1": 82, "Q54.2": 83, "Q55.1": 84, "Q55.2": 85, "Q56.1": 86, "Q56.2": 87, "Q57.1": 88, "Q57.2": 89, "Q58.1": 90, "Q58.2": 91, "Q59.1": 92, "Q59.2": 93, "Q60.1": 94, "Q60.2": 95,
		# 			"Q61.1": 96, "Q61.2": 97, "Q62.1": 98, "Q62.2": 99, "Q63.1": 100, "Q63.2": 101, "Q64.1": 102, "Q64.2": 103, "Q65.1": 104, "Q65.2": 105, "Q66.1": 106, "Q66.2": 107, "Q67.1": 108, "Q67.2": 109, "Q68.1": 110, "Q68.2": 111, "Q69.1": 112, "Q69.2": 113, "Q70.1": 114, "Q70.2": 115,
		# 			"Q71.1": 116, "Q71.2": 117, "Q72.1": 118, "Q72.2": 119, "Q73.1": 120, "Q73.2": None, "Q74.1": 121, "Q74.2": 122, "Q75.1": 123, "Q75.2": 124, "Q76.1": 125, "Q76.2": 126, "Q77.1": 127, "Q77.2": 128, "Q78.1": 129, "Q78.2": 130, "Q79.1": 131, "Q79.2": 132, "Q80.1": 133, "Q80.2": 134,
		# 			"Q81.1": 135, "Q81.2": 136, "Q82.1": 137, "Q82.2": 138, "Q83.1": 139, "Q83.2": 140, "Q84.1": 141, "Q84.2": 142, "Q85.1": 143, "Q85.2": 144, "Q86": 145, "Q87": 146, "Q88.1": None, "Q88.2": None, "Q89.1": None, "Q89.2": None, "Q90.1": None, "Q90.2": None,
		# 			"Q91.1": None, "Q91.2": None, "Q92.1": None, "Q92.2": None, "Q93.1": None, "Q93.2": None
		# 		}, num_headers=2, delimiter='\t')

		# # ADIR2003_Toddler
		# #print_codes_for_instrument('ADIR2003_Toddler')
		# filename = os.path.join(subpath, "adir_t_200401.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", "ADIR2003_Toddler", 
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: None if x[5] == '' else int(round(float(x[5]), 0)),
		# 			"interview_date": lambda x: x[4],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		}, 
		# 		{'Q002': 9, 'Q004': 14, 'Q005': 15, 'Q006': 16, 'Q007': 17, 'Q008': 18, 'Q009': 19, 
		# 		'Q010': 20, 'Q011': 21, 'Q012': 22, 'Q012E': 23, 'Q013': 24, 'Q014': 25, 'Q015.1': 26, 'Q015.2': None, 'Q015.3': None, 'Q016': 27, 'Q017': 28, 'Q018': 29, 'Q019': 30, 
		# 		'Q020': 31, 'Q021': 32, 'Q022': 33, 'Q023': 34, 'Q024': 35, 'Q025.1': 36, 'Q025.2': 37, 'Q026': 38, 'Q027': 39, 'Q028': 40, 'Q029': 41, 
		# 		'Q030': 42, 'Q031': 43, 'Q032': 44, 'Q033': 45, 'Q034': 46, 'Q035': 47, 'Q036': 48, 'Q037': 49, 'Q038': 50, 'Q039': 51, 
		# 		'Q040': 52, 'Q041': 53, 'Q042': 54, 'Q043': 55, 'Q044': 56, 'Q045': 57, 'Q046': 58, 
		# 		'Q047.01': 59, 'Q047.02': 60, 'Q047.03': 61, 'Q047.04': 62, 'Q047.05': 63, 'Q047.06': 64, 'Q047.07': 65, 'Q047.08': 66, 'Q047.09': 67, 
		# 		'Q047.10': 68, 'Q047.11': 69, 'Q047.12': 70, 'Q047.13': 71, 'Q047.14': 72, 'Q047.15': 73, 'Q047.16': 74, 'Q047.17': 75, 'Q047.18': 76, 'Q047.19': 77, 
		# 		'Q047.20': 78, 'Q047.21': 79, 'Q047.22': 80, 'Q047.23': 81, 'Q047.24': 82, 'Q047.25': 83, 'Q047.26': 84, 'Q047.27': 85, 'Q047.28': 86, 'Q047.29': 87, 
		# 		'Q047.30': 88, 'Q047.31': 89, 'Q047.32': 90, 'Q047.33': 91, 'Q047.34': 92, 'Q047.35': 93, 'Q047.36': 94, 'Q047.37': 95, 'Q047.38': 96, 'Q047.39': 97, 
		# 		'Q047.40': 98, 'Q047.41': 99, 'Q047.42': 100, 'Q047.43': 101, 'Q047.44': 102, 'Q047.45': 103, 'Q047.46': 104, 'Q047.47': 105, 'Q047.48': 106, 
		# 		'Q048': 107, 'Q049': 108, 
		# 		'Q050': 109, 'Q051': 110, 'Q052': 111, 'Q053': 112, 'Q054': 113, 'Q055': 114, 'Q056': 115, 'Q057': 116, 'Q058': 117, 'Q059': 118, 
		# 		'Q060': 119, 'Q061': 120, 'Q062': 121, 'Q063': 122, 'Q064': 123, 'Q065': 124, 'Q066.1': 125, 'Q066.2': None, 'Q066.3': None, 'Q067.1': 126, 'Q067.2': None, 'Q067.3': None, 'Q067.4': None, 'Q067.5': None, 'Q068M': 127, 'Q068F': 128, 'Q068O': 129, 'Q069': 130, 
		# 		'Q070': 131, 'Q071': 132, 'Q072': 133, 'Q073': 134, 'Q074M': 135, 'Q074F': 136, 'Q074O': 137, 'Q075': 138, 'Q076': 139, 'Q077': 140, 'Q078': 141, 'Q079': 142, 
		# 		'Q080': 143, 'Q081': 144, 'Q082M': 145, 'Q082MI': 146, 'Q082F': 147, 'Q082FI': 148, 'Q082O': 149, 'Q082OI': 150, 'Q083': None, 'Q083M': 151, 'Q083F': 152, 'Q083O': 153, 'Q084.1': 154, 'Q084.2': 155, 'Q085M': 156, 'Q085F': 157, 'Q085O': 158, 'Q086M': 159, 'Q086F': 160, 'Q086O': 161, 'Q087': 162, 'Q088': 163, 'Q089': 164, 
		# 		'Q090': 165, 'Q090.1': None, 'Q090.2': None, 'Q091': 166, 'Q092': 167, 'Q093.1': 168, 'Q093.2': 169, 'Q093.3': 170, 'Q094.1': 171, 'Q094.2': 172, 'Q094.3': 173, 'Q095.1': 174, 'Q095.2': 175, 'Q095.3': 176, 'Q096.1': 177, 'Q096.2': 178, 'Q096.3': 179, 'Q097.1': 180, 'Q097.2': 181, 'Q097.3': 182, 'Q098.1': 183, 'Q098.2': 184, 'Q098.3': 185, 'Q099.1': 186, 'Q099.2': 187, 'Q099.3': 188, 
		# 		'Q100.1': 189, 'Q100.2': 190, 'Q100.3': 191, 'Q101.1': 192, 'Q101.2': 193, 'Q101.3': 194, 'Q102.1': 195, 'Q102.2': 196, 'Q102.3': 197, 'Q103.1': 198, 'Q103.2': 199, 'Q103.3': 200, 'Q104.1': 201, 'Q104.2': 202, 'Q104.3': 203, 'Q105.1': 204, 'Q105.2': 205, 'Q105.3': 206, 'Q106.1': 207, 'Q106.2': 208, 'Q106.3': 209, 'Q107.1': 210, 'Q107.2': 211, 'Q107.3': 212, 'Q108.1': 213, 'Q108.2': 214, 'Q108.3': 215, 'Q109.1': 216, 'Q109.2': 217, 'Q109.3':218, 
		# 		'Q110.1': 219, 'Q110.2': 220, 'Q110.3': 221, 'Q111.1': 222, 'Q111.2': 223, 'Q111.3': 224, 'Q112.1': 225, 'Q112.2': 226, 'Q112.3': 227, 'Q113.1': 228, 'Q113.2': 229, 'Q113.3': 230, 'Q114.1': 231, 'Q114.2': 232, 'Q115.1': 233, 'Q115.2': 234, 'Q116.1':235, 'Q116.2': 236, 'Q117.1': 237, 'Q117.2': 238, 'Q118': 239, 'Q119': 240, 
		# 		'Q120': 241, 'Q121': 242, 'Q122': 243, 'Q123.1': 244, 'Q123.2': 245, 'Q124.1': 246, 'Q124.2': 247, 'Q125.1': 248, 'Q125.2': 249, 'Q126.1': 250, 'Q126.2': 251, 'Q127.1': 252, 'Q127.2': 253, 'Q128.1': 254, 'Q128.2': 255, 'Q129.1': 256, 'Q129.2': 257
		# 		}, num_headers=2, delimiter='\t')

		# # ADIR2003_Toddler
		# filename = os.path.join(subpath, "adir_t_200603.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", "ADIR2003_Toddler", 
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: None if x[5] == '' else int(round(float(x[5]), 0)),
		# 			"interview_date": lambda x: x[4],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		}, 
		# 		{'Q002': 8, 'Q004': 14, 'Q005': 15, 'Q006': 16, 'Q007': 17, 'Q008': 18, 'Q009': 19, 
		# 		'Q010': 20, 'Q011': 21, 'Q012': 24, 'Q012E': 25, 'Q013': 26, 'Q014': 27, 'Q015.1': 28, 'Q015.2': 29, 'Q015.3': 30, 'Q016': 31, 'Q017': 32, 'Q018': 33, 'Q019': None, 
		# 		'Q020': 34, 'Q021': 37, 'Q022': 33, 'Q023': 23, 'Q024': 44, 'Q025.1': 46, 'Q025.2': 47, 'Q026': 48, 'Q027': 49, 'Q028': 50, 'Q029': 51, 
		# 		'Q030': 52, 'Q031': 53, 'Q032': 54, 'Q033': 55, 'Q034': None, 'Q035': 56, 'Q036': 57, 'Q037': 59, 'Q038': 58, 'Q039': 60, 
		# 		'Q040': 61, 'Q041': 62, 'Q042': 63, 'Q043': 64, 'Q044': 65, 'Q045': 66, 'Q046': 45, 
		# 		'Q047.01': 68, 'Q047.02': None, 'Q047.03': None, 'Q047.04': None, 'Q047.05': None, 'Q047.06': None, 'Q047.07': 69, 'Q047.08': 70, 'Q047.09': 71, 'Q047.10': 72, 'Q047.11': 73, 'Q047.12': 74, 
		# 		'Q047.13': 75, 'Q047.14': None, 'Q047.15': None, 'Q047.16': None, 'Q047.17': None, 'Q047.18': None, 'Q047.19': 76, 'Q047.20': 77, 'Q047.21': 78, 'Q047.22': 79, 'Q047.23': 80, 'Q047.24': 81, 
		# 		'Q047.25': 82, 'Q047.26': None, 'Q047.27': None, 'Q047.28': None, 'Q047.29': None, 'Q047.30': None, 'Q047.31': 83, 'Q047.32': 84, 'Q047.33': 85, 'Q047.34': 86, 'Q047.35': 87, 'Q047.36': 88, 
		# 		'Q047.37': 89, 'Q047.38': None, 'Q047.39': None, 'Q047.40': None, 'Q047.41': None, 'Q047.42': None, 'Q047.43': 90, 'Q047.44': 91, 'Q047.45': 92, 'Q047.46': 93, 'Q047.47': 94, 'Q047.48': 95, 
		# 		'Q048': 96, 'Q049': 97, 
		# 		'Q050': 98, 'Q051': 99, 'Q052': 100, 'Q053': 102, 'Q054': 103, 'Q055': 104, 'Q056': 105, 'Q057': 106, 'Q058': 35, 'Q059': 38, 
		# 		'Q060': 39, 'Q061': 40, 'Q062': 42, 'Q063': 41, 'Q064': 36, 'Q065': 43, 'Q066.1': 107, 'Q066.2': 108, 'Q066.3': 109, 'Q067.1': None, 'Q067.2': 110, 'Q067.3': 111, 'Q067.3': 112, 'Q067.4': 113, 'Q067.5': 114, 'Q068M': 115, 'Q068F': 116, 'Q068O': 117, 'Q069': 118, 
		# 		'Q070': 119, 'Q071': 120, 'Q072': 121, 'Q073': 122, 'Q074M': 123, 'Q074F': 124, 'Q074O': 125, 'Q075': 126, 'Q076': 127, 'Q077': 128, 'Q078': 129, 'Q079': 130, 
		# 		'Q080': 131, 'Q081': 101, 'Q082M': 132, 'Q082MI': 133, 'Q082F': 134, 'Q082FI': 135, 'Q082O': 136, 'Q082OI': 137, 'Q083': 138, 'Q083M': 139, 'Q083F': 140, 'Q083O': 141, 'Q084.1': 142, 'Q084.2': 143, 'Q085M': 144, 'Q085F': 145, 'Q085O': 146, 'Q086M': 147, 'Q086F': 148, 'Q086O': 149, 'Q087': 150, 'Q088': 151, 'Q089': 152, 
		# 		'Q090': 153, 'Q090.1': 154, 'Q090.2': 155, 'Q091': 156, 'Q092': 157, 'Q093.1': 158, 'Q093.2': 159, 'Q093.3': 160, 'Q094.1': 161, 'Q094.2': 162, 'Q094.3': 163, 'Q095.1': 164, 'Q095.2': 165, 'Q095.3': 166, 'Q096.1': 167, 'Q096.2': 168, 'Q096.3': 169, 'Q097.1': 170, 'Q097.2': 171, 'Q097.3': 172, 'Q098.1': 173, 'Q098.2': 174, 'Q098.3': 175, 'Q099.1': 176, 'Q099.2': 177, 'Q099.3': 178, 
		# 		'Q100.1': 179, 'Q100.2': 180, 'Q100.3': 181, 'Q101.1': 182, 'Q101.2': 183, 'Q101.3': 184, 'Q102.1': 185, 'Q102.2': 186, 'Q102.3': 187, 'Q103.1': 188, 'Q103.2': 189, 'Q103.3': 190, 'Q104.1': 191, 'Q104.2': 192, 'Q104.3': 193, 'Q105.1': 194, 'Q105.2': 195, 'Q105.3': 196, 'Q106.1': 197, 'Q106.2': 198, 'Q106.3': 199, 'Q107.1': 200, 'Q107.2': 201, 'Q107.3': 202, 'Q108.1': 203, 'Q108.2': 204, 'Q108.3': 205, 'Q109.1': 206, 'Q109.2': 207, 'Q109.3':208, 
		# 		'Q110.1': 209, 'Q110.2': 210, 'Q110.3': 211, 'Q111.1': 212, 'Q111.2': 213, 'Q111.3': 214, 'Q112.1': 215, 'Q112.2': 216, 'Q112.3': 217, 'Q113.1': 218, 'Q113.2': 219, 'Q113.3': 220, 'Q114.1': 221, 'Q114.2': 222, 'Q115.1': 223, 'Q115.2': 224, 'Q116.1':225, 'Q116.2': 226, 'Q117.1': 227, 'Q117.2': 228, 'Q118': 229, 'Q119': 230, 
		# 		'Q120': 231, 'Q121': 232, 'Q122': 233, 'Q123.1': 234, 'Q123.2': 235, 'Q124.1': 236, 'Q124.2': 237, 'Q125.1': 238, 'Q125.2': 239, 'Q126.1': 240, 'Q126.2': 241, 'Q127.1': 242, 'Q127.2': 243, 'Q128.1': 244, 'Q128.2': 245, 'Q129.1': 246, 'Q129.2': 247
		# 		}, num_headers=2, delimiter='\t')

# 		# ADOS1
# 		filename = os.path.join(subpath, "ados1_200102.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module1", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 53, "QA02": 54, "QA03": 55, "QA04": 56, "QA05": 57, "QA06": 58, "QA07": 59, "QA08": 60, 
# 					"QB01": 61, "QB02": 62, "QB03": 63, "QB04": 64, "QB05": 65, "QB06": 66, "QB07": 67, "QB08": 68, "QB09": 69, "QB10": 70, "QB11": 71, "QB12": 72, "QB13.1": None, "QB13.2": None, "QB14": None, "QB14": None, "QB15": None, "QB16": None,
# 					"QC01": 73, "QC02": 74, 
# 					"QD01": 75, "QD02": 77, "QD03": 79, "QD04": 80, 
# 					"QE01": 82, "QE02": 83, "QE03": 84
# 				}, num_headers=2, delimiter='\t')
	
# 		# ADOS1
# 		filename = os.path.join(subpath, "ados1_200701.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module1", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				},
# 				{
# 					"QA01": 53, "QA02": 54, "QA03": 55, "QA04": 56, "QA05": 57, "QA06": 58, "QA07": 59, "QA08": 60, 
# 					"QB01": 61, "QB02": 62, "QB03": 63, "QB04": 64, "QB05": 65, "QB06": 66, "QB07": 67, "QB08": 68, "QB09": 69, "QB10": 70, "QB11": 71, "QB12": 72, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 					"QC01": 73, "QC02": 74, 
# 					"QD01": 75, "QD02": 77, "QD03": 79, "QD04": 80, 
# 					"QE01": 82, "QE02": 83, "QE03": 84
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS1
# 		filename = os.path.join(subpath, "ados1_201201.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module1", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 20, "QA02": 21, "QA03": 22, "QA04": 23, "QA05": 24, "QA06": 25, "QA07": 26, "QA08": 27, 
# 					"QB01": 28, "QB02": 29, "QB03": 30, "QB04": 31, "QB05": 32, "QB06": 33, "QB07": 34, "QB08": 35, "QB09": 36, "QB10": 37, "QB11": 38, "QB12": 39, "QB13.1": 40, "QB13.2": 41, "QB14": 42, "QB15": 43, "QB16": 44,
# 					"QC01": 45, "QC02": 46, 
# 					"QD01": 47, "QD02": 49, "QD03": 41, "QD04": 42, 
# 					"QE01": 54, "QE02": 55, "QE03": 56
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS2
# 		# If we see a directory, and it has an ados file, then read it
# 		filename = os.path.join(subpath, "ados2_200102.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module2", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 40, "QA02": 42, "QA03": 43, "QA04": 44, "QA05": 45, "QA06": 46, "QA07": 47, 
# 					"QB01": 48, "QB02": 49, "QB03": 50, "QB04": 51, "QB05": 52, "QB06": 53, "QB07": 54, "QB08": 55, "QB09.1": None, "QB09.2": None, "QB10": 56, "QB11": 57, "QB12": 58,
# 					"QC01": 59, "QC02": 60, 
# 					"QD01": 61, "QD02": 63, "QD03": 65, "QD04": 66, 
# 					"QE01": 68, "QE02": 69, "QE03": 70
# 				}, num_headers=2, delimiter='\t')
	
# 		# ADOS2
# 		filename = os.path.join(subpath, "ados2_200701.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module2", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 40, "QA02": 42, "QA03": 43, "QA04": 44, "QA05": 45, "QA06": 46, "QA07": 47, 
# 					"QB01": 48, "QB02": 49, "QB03": 50, "QB04": 51, "QB05": 52, "QB06": 53, "QB07": 54, "QB08": 55, "QB09.1": None, "QB09.2": None, "QB10": 56, "QB11": 57, "QB12": 58,
# 					"QC01": 59, "QC02": 60, 
# 					"QD01": 61, "QD02": 63, "QD03": 65, "QD04": 66, 
# 					"QE01": 68, "QE02": 69, "QE03": 70
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS2
# 		filename = os.path.join(subpath, "ados2_201201.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module2", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				},
# 				{
# 					"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, 
# 					"QB01": 31, "QB02": 32, "QB03": 33, "QB04": 34, "QB05": 35, "QB06": 36, "QB07": 37, "QB08": 38, "QB09.1": 39, "QB09.2": 40, "QB10": 41, "QB11": 42, "QB12": 43,
# 					"QC01": 44, "QC02": 45, 
# 					"QD01": 46, "QD02": 47, "QD03": 48, "QD04": 49, 
# 					"QE01": 50, "QE02": 51, "QE03": 52
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS3
# 		# If we see a directory, and it has an ados file, then read it
# 		filename = os.path.join(subpath, "ados3_200102.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module3", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31, 
# 					"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": None, "QB09": 29, "QB10": 40, "QB11": 41,
# 					"QC01": 42, 
# 					"QD01": 43, "QD02": 45, "QD03": 47, "QD04": 48,  "QD05": 49,
# 					"QE01": 51, "QE02": 52, "QE03": 53
# 				}, num_headers=2, delimiter='\t')
	
# 		# ADOS3
# 		filename = os.path.join(subpath, "ados3_200701.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module3", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31, 
# 					"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": None, "QB09": 29, "QB10": 40, "QB11": 41,
# 					"QC01": 42, 
# 					"QD01": 43, "QD02": 45, "QD03": 47, "QD04": 48,  "QD05": 49,
# 					"QE01": 51, "QE02": 52, "QE03": 53
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS3
# 		filename = os.path.join(subpath, "ados3_201201.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module3", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 23, "QA02": 24, "QA03": 25, "QA04": 26, "QA05": 27, "QA06": 28, "QA07": 29, "QA08": 30, "QA09": 31,   
# 					"QB01": 32, "QB02": 33, "QB03": 34, "QB04": 35, "QB05": 36, "QB06": 37, "QB07": 38, "QB08": 39, "QB09": 40, "QB10": 41, "QB11": 42,
# 					"QC01": 43, 
# 					"QD01": 44, "QD02": 46, "QD03": 48, "QD04": 49, "QD05": 50,
# 					"QE01": 52, "QE02": 53, "QE03": 54
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS4
# 		filename = os.path.join(subpath, "ados4_200102.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "ADOS_Module4", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[7] == "M" else ("Female" if x[7] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: None if x[5].strip() == '' else int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, "QA08": 31, "QA09": 32, "QA10": 33, 
# 					"QB01": 34, "QB02": 35, "QB03": 36, "QB04": 37, "QB05": 38, "QB06": 39, "QB07": 40, "QB08": 41, "QB09": 42, "QB10": None, "QB11": 43, "QB12": 44, "QB13": 45,
# 					"QC01": 46, 
# 					"QD01": 47, "QD02": 49, "QD03": 51, "QD04": 52,  "QD05": 53,
# 					"QE01": 55, "QE02": 56, "QE03": 57
# 				}, num_headers=2, delimiter='\t')

# 		# ADOS4
# 		filename = os.path.join(subpath, "ados4_201201.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(os.path.join(subpath, "ados4_201201.txt"), "National Database for Autism Research", "ADOS_Module4", 
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				{
# 					"QA01": 24, "QA02": 25, "QA03": 26, "QA04": 27, "QA05": 28, "QA06": 29, "QA07": 30, "QA08": 31, "QA09": 32, "QA10": 33, 
# 					"QB01": 34, "QB02": 35, "QB03": 36, "QB04": 37, "QB05": 38, "QB06": 39, "QB07": 40, "QB08": 41, "QB09": 42, "QB10": 43, "QB11": 44, "QB12": 45, "QB13": 46,
# 					"QC01": 47, 
# 					"QD01": 48, "QD02": 50, "QD03": 52, "QD04": 53,  "QD05": 54,
# 					"QE01": 56, "QE02": 57, "QE03": 58
# 				}, num_headers=2, delimiter='\t')

# 		# SRS
# 		filename = os.path.join(subpath, "srs02.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "SRS_Child",
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(37, 102))),
# 				value_transform=srs_transform, num_headers=2, delimiter='\t')

# 		# SRS
# 		filename = os.path.join(subpath, "srs_adult03.txt")
# 		if os.path.isfile("%s/%s" % (directory, filename)):
# 			convert_phenotypes(filename, "National Database for Autism Research", "SRS_Adult",
# 				{
# 					"identifier": identifier_lambda,
# 					"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
# 					"race": lambda x: None,
# 					"ethnicity": lambda x: None,
# 					"age": lambda x: int(round(float(x[5]), 0)),
# 					"interview_date": lambda x: x[4],
# 					"family": lambda x: None,
# 					"clinical_diagnosis_raw": clinical_diagnosis_lambda
# 				}, 
# 				dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(25, 90))), 
# 				value_transform=srs_transform, num_headers=2, delimiter='\t')

		# # SRS
		# filename = os.path.join(subpath, "srs201.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", "SRS_Child",
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: int(round(float(x[5]), 0)),
		# 			"interview_date": lambda x: x[4],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		}, 
		# 		dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(13, 78))), 
		# 		value_transform=srs_transform, num_headers=2, delimiter='\t')

		# # SRS
		# filename = os.path.join(subpath, "srs_preschool_200601.txt")
		# if os.path.isfile("%s/%s" % (directory, filename)):
		# 	convert_phenotypes(filename, "National Database for Autism Research", "SRS_Preschool",
		# 		{
		# 			"identifier": identifier_lambda,
		# 			"gender": lambda x: "Male" if x[6] == "M" else ("Female" if x[6] == "F" else None),
		# 			"race": lambda x: None,
		# 			"ethnicity": lambda x: None,
		# 			"age": lambda x: int(round(float(x[5]), 0)),
		# 			"interview_date": lambda x: x[4],
		# 			"family": lambda x: None,
		# 			"clinical_diagnosis_raw": clinical_diagnosis_lambda
		# 		}, 
		# 		dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(11, 76))), 
		# 		value_transform=srs_transform, num_headers=2, delimiter='\t')

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- SSC ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# # pull diagnosis
# ssc_diagnosis = {}
# ssc_demographics = {}
# with open(directory + "/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_core_descriptive.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	ssc_demographics.update([(x[0], x[1:]) for x in reader])

# with open(directory + "/SSC Version 15 Phenotype Data Set 2/Proband Data/ssc_diagnosis.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	ssc_diagnosis.update([(x[0], x[15]) for x in reader])

# with open(directory + "/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ssc_core_descriptive.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	ssc_demographics.update([(x[0], x[1:]) for x in reader])

# with open(directory + "/SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ssc_diagnosis.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	ssc_diagnosis.update([(x[0], x[15]) for x in reader])

# # ADIR2003
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/adi_r.csv", "Simons Simplex Collection", "ADIR2003", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"Q02": (2, 3), "Q04": 4, "Q05": (5, 6), "Q06": (7, 8), "Q07": (9, 10), "Q08": (11, 12), "Q09": (13, 14), "Q10": (15, 16),
# 		"Q11": 17, "Q12": 18, "Q13": 19, "Q14": 20, "Q15": 21, "Q16": 22, "Q17": (23, 24), "Q18": 25, "Q19": (26, 27), "Q20": 28,
# 		"Q21": 29, "Q22": 30, "Q23": 31, "Q24": 32, "Q25": 33, "Q26": (34, 35), "Q27": 36, "Q28": (37, 38), "Q29.1": 39, "Q29.2": 40, "Q30": 41,
# 		"Q31.1": 42, "Q31.2": 43, "Q32.1": 44, "Q32.2": 45, "Q33.1": 46, "Q33.2": 47, "Q34.1": 48, "Q34.2": 49, "Q35.1": 50, "Q35.2": 51, "Q36.1": 52, "Q36.2": 53, "Q37.1": 54, "Q37.2": 55, "Q38.1": 56, "Q38.2": 57, "Q39.1": 58, "Q39.2": 59, "Q40.1": 60, "Q40.2": 61,
# 		"Q41.1": 62, "Q41.2": 63, "Q42.1": 64, "Q42.2": 65, "Q43.1": 66, "Q43.2": 67, "Q44.1": 68, "Q44.2": 69, "Q45.1": 70, "Q45.2": 71, "Q46.1": 72, "Q46.2": 73, "Q47.1": 74, "Q47.2": 75, "Q48.1": 76, "Q48.2": 77, "Q49.1": 78, "Q49.2": 79, "Q50.1": 80, "Q50.2": 81,
# 		"Q51.1": 82, "Q51.2": 83, "Q52.1": 84, "Q52.2": 85, "Q53.1": 86, "Q53.2": 87, "Q54.1": 88, "Q54.2": 89, "Q55.1": 90, "Q55.2": 91, "Q56.1": 92, "Q56.2": 93, "Q57.1": 94, "Q57.2": 95, "Q58.1": 96, "Q58.2": 97, "Q59.1": 98, "Q59.2": 99, "Q60.1": 100, "Q60.2": 101,
# 		"Q61.1": 102, "Q61.2": 103, "Q62.1": 104, "Q62.2": 105, "Q63.1": 106, "Q63.2": 107, "Q64.1": 108, "Q64.2": 109, "Q65.1": 110, "Q65.2": 111, "Q66.1": 112, "Q66.2": 113, "Q67.1": 114, "Q67.2": 115, "Q68.1": 116, "Q68.2": 117, "Q69.1": 118, "Q69.2": 119, "Q70.1": 120, "Q70.2": 121,
# 		"Q71.1": 122, "Q71.2": 123, "Q72.1": 124, "Q72.2": 125, "Q73.1": 126, "Q73.2": 127, "Q74.1": 128, "Q74.2": 129, "Q75.1": 130, "Q75.2": 131, "Q76.1": 132, "Q76.2": 133, "Q77.1": 134, "Q77.2": 135, "Q78.1": 136, "Q78.2": 137, "Q79.1": 138, "Q79.2": 139, "Q80.1": 140, "Q80.2": 141,
# 		"Q81.1": 142, "Q81.2": 143, "Q82.1": 144, "Q82.2": 145, "Q83.1": 146, "Q83.2": 147, "Q84.1": 148, "Q84.2": 149, "Q85.1": 150, "Q85.2": 151, "Q86": 152, "Q87": (153, 154), "Q88.1": 155, "Q88.2": 156, "Q89.1": 157, "Q89.2": 158, "Q90.1": 159, "Q90.2": 160,
# 		"Q91.1": 161, "Q91.2": 162, "Q92.1": 163, "Q92.2": 164, "Q93.1": 165, "Q93.2": 166
# 	})

# # ADIR2003
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/adi_r.csv", "Simons Simplex Collection", "ADIR2003", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"Q02": (2, 3), "Q04": 4, "Q05": (5, 6), "Q06": (7, 8), "Q07": (9, 10), "Q08": (11, 12), "Q09": (13, 14), "Q10": (15, 16),
# 		"Q11": 17, "Q12": 18, "Q13": 19, "Q14": 20, "Q15": 21, "Q16": 22, "Q17": (23, 24), "Q18": 25, "Q19": (26, 27), "Q20": 28,
# 		"Q21": 29, "Q22": 30, "Q23": 31, "Q24": 32, "Q25": 33, "Q26": (34, 35), "Q27": 36, "Q28": (37, 38), "Q29.1": 39, "Q29.2": 40, "Q30": 41,
# 		"Q31.1": 42, "Q31.2": 43, "Q32.1": 44, "Q32.2": 45, "Q33.1": 46, "Q33.2": 47, "Q34.1": 48, "Q34.2": 49, "Q35.1": 50, "Q35.2": 51, "Q36.1": 52, "Q36.2": 53, "Q37.1": 54, "Q37.2": 55, "Q38.1": 56, "Q38.2": 57, "Q39.1": 58, "Q39.2": 59, "Q40.1": 60, "Q40.2": 61,
# 		"Q41.1": 62, "Q41.2": 63, "Q42.1": 64, "Q42.2": 65, "Q43.1": 66, "Q43.2": 67, "Q44.1": 68, "Q44.2": 69, "Q45.1": 70, "Q45.2": 71, "Q46.1": 72, "Q46.2": 73, "Q47.1": 74, "Q47.2": 75, "Q48.1": 76, "Q48.2": 77, "Q49.1": 78, "Q49.2": 79, "Q50.1": 80, "Q50.2": 81,
# 		"Q51.1": 82, "Q51.2": 83, "Q52.1": 84, "Q52.2": 85, "Q53.1": 86, "Q53.2": 87, "Q54.1": 88, "Q54.2": 89, "Q55.1": 90, "Q55.2": 91, "Q56.1": 92, "Q56.2": 93, "Q57.1": 94, "Q57.2": 95, "Q58.1": 96, "Q58.2": 97, "Q59.1": 98, "Q59.2": 99, "Q60.1": 100, "Q60.2": 101,
# 		"Q61.1": 102, "Q61.2": 103, "Q62.1": 104, "Q62.2": 105, "Q63.1": 106, "Q63.2": 107, "Q64.1": 108, "Q64.2": 109, "Q65.1": 110, "Q65.2": 111, "Q66.1": 112, "Q66.2": 113, "Q67.1": 114, "Q67.2": 115, "Q68.1": 116, "Q68.2": 117, "Q69.1": 118, "Q69.2": 119, "Q70.1": 120, "Q70.2": 121,
# 		"Q71.1": 122, "Q71.2": 123, "Q72.1": 124, "Q72.2": 125, "Q73.1": 126, "Q73.2": 127, "Q74.1": 128, "Q74.2": 129, "Q75.1": 130, "Q75.2": 131, "Q76.1": 132, "Q76.2": 133, "Q77.1": 134, "Q77.2": 135, "Q78.1": 136, "Q78.2": 137, "Q79.1": 138, "Q79.2": 139, "Q80.1": 140, "Q80.2": 141,
# 		"Q81.1": 142, "Q81.2": 143, "Q82.1": 144, "Q82.2": 145, "Q83.1": 146, "Q83.2": 147, "Q84.1": 148, "Q84.2": 149, "Q85.1": 150, "Q85.2": 151, "Q86": 152, "Q87": (153, 154), "Q88.1": 155, "Q88.2": 156, "Q89.1": 157, "Q89.2": 158, "Q90.1": 159, "Q90.2": 160,
# 		"Q91.1": 161, "Q91.2": 162, "Q92.1": 163, "Q92.2": 164, "Q93.1": 165, "Q93.2": 166
# 	})

# # ADOS1
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/ados_1_raw.csv", "Simons Simplex Collection", "ADOS_Module1", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, 
# 		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09": 18, "QB10": 19, "QB11": 20, "QB12": 21, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 		"QC01": 22, "QC02": 23, 
# 		"QD01": 24, "QD02": 25, "QD03": 26, "QD04": 27, 
# 		"QE01": 28, "QE02": 29, "QE03": 30
# 	})

# # ADOS1
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_1_raw.csv", "Simons Simplex Collection", "ADOS_Module1", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, 
# 		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09": 18, "QB10": 19, "QB11": 20, "QB12": 21, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 		"QC01": 22, "QC02": 23, 
# 		"QD01": 24, "QD02": 25, "QD03": 26, "QD04": 27, 
# 		"QE01": 28, "QE02": 29, "QE03": 30
# 	})

# # ADOS2
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/ados_2_raw.csv", "Simons Simplex Collection", "ADOS_Module2", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 4, "QA03": 5, "QA04": 6, "QA05": 7, "QA06": 8, "QA07": 9,
# 		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09.1": None, "QB09.2": None, "QB10": 18, "QB11": 19, "QB12": 20,
# 		"QC01": 21, "QC02": 22, 
# 		"QD01": 23, "QD02": 24, "QD03": 25, "QD04": 26, 
# 		"QE01": 27, "QE02": 28, "QE03": 29
# 	})

# # ADOS2
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_2_raw.csv", "Simons Simplex Collection", "ADOS_Module2", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 4, "QA03": 5, "QA04": 6, "QA05": 7, "QA06": 8, "QA07": 9,
# 		"QB01": 10, "QB02": 11, "QB03": 12, "QB04": 13, "QB05": 14, "QB06": 15, "QB07": 16, "QB08": 17, "QB09.1": None, "QB09.2": None, "QB10": 18, "QB11": 19, "QB12": 20,
# 		"QC01": 21, "QC02": 22, 
# 		"QD01": 23, "QD02": 24, "QD03": 25, "QD04": 26, 
# 		"QE01": 27, "QE02": 28, "QE03": 29
# 	})

# # ADOS3
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/ados_3_raw.csv", "Simons Simplex Collection", "ADOS_Module3", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10,
# 		"QB01": 11, "QB02": 12, "QB03": 13, "QB04": 14, "QB05": 15, "QB06": 16, "QB07": 17, "QB08": None, "QB09": 18, "QB10": 19, "QB11": 20,
# 		"QC01": 21,
# 		"QD01": 22, "QD02": 23, "QD03": 24, "QD04": 25, "QD05": 26, 
# 		"QE01": 27, "QE02": 28, "QE03": 29
# 	})

# # ADOS3
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_3_raw.csv", "Simons Simplex Collection", "ADOS_Module3", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10,
# 		"QB01": 11, "QB02": 12, "QB03": 13, "QB04": 14, "QB05": 15, "QB06": 16, "QB07": 17, "QB08": None, "QB09": 18, "QB10": 19, "QB11": 20,
# 		"QC01": 21,
# 		"QD01": 22, "QD02": 23, "QD03": 24, "QD04": 25, "QD05": 26, 
# 		"QE01": 27, "QE02": 28, "QE03": 29
# 	})

# # ADOS4	
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/ados_4_raw.csv", "Simons Simplex Collection", "ADOS_Module4", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10, "QA10": 11,
# 		"QB01": 12, "QB02": 13, "QB03": 14, "QB04": 15, "QB05": 16, "QB06": 17, "QB07": 18, "QB08": 19, "QB09": 20, "QB10": None, "QB11": 21, "QB12": 22, "QB13": 23,
# 		"QC01": 24,
# 		"QD01": 25, "QD02": 26, "QD03": 27, "QD04": 28, "QD05": 29, 
# 		"QE01": 30, "QE02": 31, "QE03": 32
# 	})

# # ADOS4
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/ados_4_raw.csv", "Simons Simplex Collection", "ADOS_Module4", 
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 2, "QA02": 3, "QA03": 4, "QA04": 5, "QA05": 6, "QA06": 7, "QA07": 8, "QA08": 9, "QA09": 10, "QA10": 11,
# 		"QB01": 12, "QB02": 13, "QB03": 14, "QB04": 15, "QB05": 16, "QB06": 17, "QB07": 18, "QB08": 19, "QB09": 20, "QB10": None, "QB11": 21, "QB12": 22, "QB13": 23,
# 		"QC01": 24,
# 		"QD01": 25, "QD02": 26, "QD03": 27, "QD04": 28, "QD05": 29, 
# 		"QE01": 30, "QE02": 31, "QE03": 32
# 	})

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Proband Data/srs_parent_recode.csv", "Simons Simplex Collection", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/MZ Twin Data/srs_parent_recode.csv", "Simons Simplex Collection", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Other Sibling Data/srs_parent_recode.csv", "Simons Simplex Collection", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/srs_parent_recode.csv", "Simons Simplex Collection", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Father Data/srs_adult_recode.csv", "Simons Simplex Collection", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Mother Data/srs_adult_recode.csv", "Simons Simplex Collection", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Other Sibling Data/srs_adult_recode.csv", "Simons Simplex Collection", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # SRS
# convert_phenotypes("SSC Version 15 Phenotype Data Set 2/Designated Unaffected Sibling Data/srs_adult_recode.csv", "Simons Simplex Collection", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][39].title(),
# 		"race": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][34],
# 		"ethnicity": lambda x: None if x[0] not in ssc_demographics else ssc_demographics[x[0]][20],
# 		"age": lambda x: None if x[0] not in ssc_demographics or ssc_demographics[x[0]][13] == '' else int(ssc_demographics[x[0]][13]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0][:-3],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in ssc_diagnosis else ssc_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(3, 68))))

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- Cognoa Controls ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# # ADIR
# convert_phenotypes("cognoa_adir_dataset.txt", "Cognoa", "ADIR2003", 
# 	{
# 		"identifier": lambda x: x[158],
# 		"gender": lambda x: None if x[156] == '' else x[156].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] == '' else int(x[0]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: None,
# 		"clinical_diagnosis_raw": lambda x: 'Control'
# 	}, 
# 	{
# 		"Q02": 2, "Q04": 3, "Q05": 4, "Q06": 5, "Q07": 6, "Q08": 7, "Q09": 8, "Q10": 9,
# 		"Q11": 10, "Q12": 11, "Q13": 12, "Q14": 13, "Q15": 14, "Q16": 15, "Q17": 16, "Q18": 17, "Q19": 18, "Q20": 19,
# 		"Q21": 20, "Q22": 21, "Q23": 22, "Q24": 23, "Q25": 24, "Q26": 25, "Q27": 26, "Q28": 27, "Q29.1": 28, "Q29.2": 29, "Q30": 30,
# 		"Q31.1": 31, "Q31.2": 32, "Q32.1": 33, "Q32.2": 34, "Q33.1": 35, "Q33.2": 36, "Q34.1": 37, "Q34.2": 38, "Q35.1": 39, "Q35.2": 40, "Q36.1": 41, "Q36.2": 42, "Q37.1": 43, "Q37.2": 44, "Q38.1": 45, "Q38.2": 46, "Q39.1": 47, "Q39.2": 48, "Q40.1": 49, "Q40.2": 50,
# 		"Q41.1": 51, "Q41.2": 52, "Q42.1": 53, "Q42.2": 54, "Q43.1": 55, "Q43.2": 56, "Q44.1": 57, "Q44.2": 58, "Q45.1": 59, "Q45.2": 60, "Q46.1": 61, "Q46.2": 62, "Q47.1": 63, "Q47.2": 64, "Q48.1": 65, "Q48.2": 66, "Q49.1": 67, "Q49.2": 68, "Q50.1": 69, "Q50.2": 70,
# 		"Q51.1": 71, "Q51.2": 72, "Q52.1": 73, "Q52.2": 74, "Q53.1": 75, "Q53.2": 76, "Q54.1": 77, "Q54.2": 78, "Q55.1": 79, "Q55.2": 80, "Q56.1": 81, "Q56.2": 82, "Q57.1": 83, "Q57.2": 84, "Q58.1": 85, "Q58.2": 86, "Q59.1": 87, "Q59.2": 88, "Q60.1": 89, "Q60.2": 90,
# 		"Q61.1": 91, "Q61.2": 92, "Q62.1": 93, "Q62.2": 94, "Q63.1": 95, "Q63.2": 96, "Q64.1": 97, "Q64.2": 98, "Q65.1": 99, "Q65.2": 100, "Q66.1": 101, "Q66.2": 102, "Q67.1": 103, "Q67.2": 104, "Q68.1": 105, "Q68.2": 106, "Q69.1": 107, "Q69.2": 108, "Q70.1": 109, "Q70.2": 110,
# 		"Q71.1": 111, "Q71.2": 112, "Q72.1": 113, "Q72.2": 114, "Q73.1": 115, "Q73.2": 116, "Q74.1": 117, "Q74.2": 118, "Q75.1": 119, "Q75.2": 120, "Q76.1": 121, "Q76.2": 122, "Q77.1": 123, "Q77.2": 124, "Q78.1": 125, "Q78.2": 126, "Q79.1": 127, "Q79.2": 128, "Q80.1": 129, "Q80.2": 130,
# 		"Q81.1": 131, "Q81.2": 132, "Q82.1": 133, "Q82.2": 134, "Q83.1": 135, "Q83.2": 136, "Q84.1": 137, "Q84.2": 138, "Q85.1": 139, "Q85.2": 140, "Q86": 141, "Q87": 142, "Q88.1": 143, "Q88.2": 144, "Q89.1": 145, "Q89.2": 146, "Q90.1": 147, "Q90.2": 148,
# 		"Q91.1": 149, "Q91.2": 150, "Q92.1": 151, "Q92.2": 152, "Q93.1": 153, "Q93.2": 154
# 	}, delimiter='\t')

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- SVIP ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# # Pull diagnosis
# svip_diagnosis = {}
# with open(directory + "/SVIP/SVIP_1q21.1/diagnosis_summary.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	svip_diagnosis.update([(x[0], 'Control' if x[16]=='FALSE' else x[72]) for x in reader])

# with open(directory + "/SVIP/SVIP_16p11.2/diagnosis_summary.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	svip_diagnosis.update([(x[0], 'Control' if x[16]=='FALSE' else x[72]) for x in reader])

# svip_demo = {}
# with open(directory + "/SVIP/SVIP_1q21.1/svip_subjects.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	svip_demo.update([(x[0], x) for x in reader])

# with open(directory + "/SVIP/SVIP_16p11.2/svip_subjects.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)[1:]
# 	svip_demo.update([(x[0], x) for x in reader])

# # ADIR2003
# convert_phenotypes("SVIP/Longitudinal/adi_r.csv", "SVIP", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[3],
# 		"gender": lambda x: None if x[3] not in svip_demo else svip_demo[x[3]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: int(x[5]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: x[0],
# 		"clinical_diagnosis_raw": lambda x: None if x[3] not in svip_diagnosis else svip_diagnosis[x[3]]
# 	}, 
# 	{
# 		"Q02": (6, 7), "Q04": 8, "Q05": (9, 10), "Q06": (11, 12), "Q07": (13, 14), "Q08": (15, 16), "Q09": (17, 18), "Q10": (19, 20),
# 		"Q11": 21, "Q12": 22, "Q13": 23, "Q14": 24, "Q15": 25, "Q16": 26, "Q17": (27, 28), "Q18": 29, "Q19": (30, 31), "Q20": 32,
# 		"Q21": 33, "Q22": 34, "Q23": 35, "Q24": 36, "Q25": 37, "Q26": (38, 39), "Q27": 40, "Q28": (41, 42), "Q29.1": 43, "Q29.2": 44, "Q30": 45,
# 		"Q31.1": 46, "Q31.2": 47, "Q32.1": 48, "Q32.2": 49, "Q33.1": 50, "Q33.2": 51, "Q34.1": 52, "Q34.2": 53, "Q35.1": 54, "Q35.2": 55, "Q36.1": 56, "Q36.2": 57, "Q37.1": 58, "Q37.2": 59, "Q38.1": 60, "Q38.2": 61, "Q39.1": 62, "Q39.2": 63, "Q40.1": 64, "Q40.2": 65,
# 		"Q41.1": 66, "Q41.2": 67, "Q42.1": 68, "Q42.2": 69, "Q43.1": 70, "Q43.2": 71, "Q44.1": 72, "Q44.2": 73, "Q45.1": 74, "Q45.2": 75, "Q46.1": 76, "Q46.2": 77, "Q47.1": 78, "Q47.2": 79, "Q48.1": 80, "Q48.2": 81, "Q49.1": 82, "Q49.2": 83, "Q50.1": 84, "Q50.2": 85,
# 		"Q51.1": 86, "Q51.2": 87, "Q52.1": 88, "Q52.2": 89, "Q53.1": 90, "Q53.2": 91, "Q54.1": 92, "Q54.2": 93, "Q55.1": 94, "Q55.2": 95, "Q56.1": 96, "Q56.2": 97, "Q57.1": 98, "Q57.2": 99, "Q58.1": 100, "Q58.2": 101, "Q59.1": 102, "Q59.2": 103, "Q60.1": 104, "Q60.2": 105,
# 		"Q61.1": 106, "Q61.2": 107, "Q62.1": 108, "Q62.2": 109, "Q63.1": 110, "Q63.2": 111, "Q64.1": 112, "Q64.2": 113, "Q65.1": 114, "Q65.2": 115, "Q66.1": 116, "Q66.2": 117, "Q67.1": 118, "Q67.2": 119, "Q68.1": 120, "Q68.2": 121, "Q69.1": 122, "Q69.2": 123, "Q70.1": 124, "Q70.2": 125,
# 		"Q71.1": 126, "Q71.2": 127, "Q72.1": 128, "Q72.2": 129, "Q73.1": 130, "Q73.2": 131, "Q74.1": 132, "Q74.2": 133, "Q75.1": 134, "Q75.2": 135, "Q76.1": 136, "Q76.2": 137, "Q77.1": 138, "Q77.2": 139, "Q78.1": 140, "Q78.2": 141, "Q79.1": 142, "Q79.2": 143, "Q80.1": 144, "Q80.2": 145,
# 		"Q81.1": 146, "Q81.2": 147, "Q82.1": 148, "Q82.2": 149, "Q83.1": 150, "Q83.2": 151, "Q84.1": 152, "Q84.2": 153, "Q85.1": 154, "Q85.2": 155, "Q86": 156, "Q87": (157, 158), "Q88.1": 159, "Q88.2": 160, "Q89.1": 161, "Q89.2": 162, "Q90.1": 163, "Q90.2": 164,
# 		"Q91.1": 165, "Q91.2": 166, "Q92.1": 167, "Q92.2": 168, "Q93.1": 169, "Q93.2": 170
# 	})

# # ADIR2003
# convert_phenotypes("SVIP/SVIP_1q21.1/adi_r.csv", "SVIP", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	{
# 		"Q02": (27, 28), "Q04": 29, "Q05": (30, 31), "Q06": (32, 33), "Q07": (34, 35), "Q08": (36, 37), "Q09": (38, 39), "Q10": (40, 41),
# 		"Q11": 42, "Q12": 43, "Q13": 44, "Q14": 45, "Q15": 46, "Q16": 47, "Q17": (48, 49), "Q18": 50, "Q19": (51, 52), "Q20": 53,
# 		"Q21": 54, "Q22": 55, "Q23": 56, "Q24": 57, "Q25": 58, "Q26": (59, 60), "Q27": 61, "Q28": (62, 63), "Q29.1": 64, "Q29.2": 65, "Q30": 66,
# 		"Q31.1": 67, "Q31.2": 68, "Q32.1": 69, "Q32.2": 70, "Q33.1": 71, "Q33.2": 72, "Q34.1": 73, "Q34.2": 74, "Q35.1": 75, "Q35.2": 76, "Q36.1": 77, "Q36.2": 78, "Q37.1": 79, "Q37.2": 80, "Q38.1": 81, "Q38.2": 82, "Q39.1": 83, "Q39.2": 84, "Q40.1": 85, "Q40.2": 86,
# 		"Q41.1": 87, "Q41.2": 88, "Q42.1": 89, "Q42.2": 90, "Q43.1": 91, "Q43.2": 92, "Q44.1": 93, "Q44.2": 94, "Q45.1": 95, "Q45.2": 96, "Q46.1": 97, "Q46.2": 98, "Q47.1": 99, "Q47.2": 100, "Q48.1": 101, "Q48.2": 102, "Q49.1": 103, "Q49.2": 104, "Q50.1": 105, "Q50.2": 106,
# 		"Q51.1": 107, "Q51.2": 108, "Q52.1": 109, "Q52.2": 110, "Q53.1": 111, "Q53.2": 112, "Q54.1": 113, "Q54.2": 114, "Q55.1": 115, "Q55.2": 116, "Q56.1": 117, "Q56.2": 118, "Q57.1": 119, "Q57.2": 120, "Q58.1": 121, "Q58.2": 122, "Q59.1": 123, "Q59.2": 124, "Q60.1": 125, "Q60.2": 126,
# 		"Q61.1": 127, "Q61.2": 128, "Q62.1": 129, "Q62.2": 130, "Q63.1": 131, "Q63.2": 132, "Q64.1": 133, "Q64.2": 134, "Q65.1": 135, "Q65.2": 136, "Q66.1": 137, "Q66.2": 138, "Q67.1": 139, "Q67.2": 140, "Q68.1": 141, "Q68.2": 142, "Q69.1": 143, "Q69.2": 144, "Q70.1": 145, "Q70.2": 146,
# 		"Q71.1": 147, "Q71.2": 148, "Q72.1": 149, "Q72.2": 150, "Q73.1": 151, "Q73.2": 152, "Q74.1": 153, "Q74.2": 154, "Q75.1": 155, "Q75.2": 156, "Q76.1": 157, "Q76.2": 158, "Q77.1": 159, "Q77.2": 160, "Q78.1": 161, "Q78.2": 162, "Q79.1": 163, "Q79.2": 164, "Q80.1": 165, "Q80.2": 166,
# 		"Q81.1": 167, "Q81.2": 168, "Q82.1": 169, "Q82.2": 170, "Q83.1": 171, "Q83.2": 172, "Q84.1": 173, "Q84.2": 174, "Q85.1": 175, "Q85.2": 176, "Q86": 177, "Q87": (178, 179), "Q88.1": 180, "Q88.2": 181, "Q89.1": 182, "Q89.2": 183, "Q90.1": 184, "Q90.2": 185,
# 		"Q91.1": 186, "Q91.2": 187, "Q92.1": 188, "Q92.2": 189, "Q93.1": 190, "Q93.2": 191
# 	})

# # ADIR2003
# convert_phenotypes("SVIP/SVIP_16p11.2/adi_r.csv", "SVIP", "ADIR2003",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	{
# 		"Q02": (27, 28), "Q04": 29, "Q05": (30, 31), "Q06": (32, 33), "Q07": (34, 35), "Q08": (36, 37), "Q09": (38, 39), "Q10": (40, 41),
# 		"Q11": 42, "Q12": 43, "Q13": 44, "Q14": 45, "Q15": 46, "Q16": 47, "Q17": (48, 49), "Q18": 50, "Q19": (51, 52), "Q20": 53,
# 		"Q21": 54, "Q22": 55, "Q23": 56, "Q24": 57, "Q25": 58, "Q26": (59, 60), "Q27": 61, "Q28": (62, 63), "Q29.1": 64, "Q29.2": 65, "Q30": 66,
# 		"Q31.1": 67, "Q31.2": 68, "Q32.1": 69, "Q32.2": 70, "Q33.1": 71, "Q33.2": 72, "Q34.1": 73, "Q34.2": 74, "Q35.1": 75, "Q35.2": 76, "Q36.1": 77, "Q36.2": 78, "Q37.1": 79, "Q37.2": 80, "Q38.1": 81, "Q38.2": 82, "Q39.1": 83, "Q39.2": 84, "Q40.1": 85, "Q40.2": 86,
# 		"Q41.1": 87, "Q41.2": 88, "Q42.1": 89, "Q42.2": 90, "Q43.1": 91, "Q43.2": 92, "Q44.1": 93, "Q44.2": 94, "Q45.1": 95, "Q45.2": 96, "Q46.1": 97, "Q46.2": 98, "Q47.1": 99, "Q47.2": 100, "Q48.1": 101, "Q48.2": 102, "Q49.1": 103, "Q49.2": 104, "Q50.1": 105, "Q50.2": 106,
# 		"Q51.1": 107, "Q51.2": 108, "Q52.1": 109, "Q52.2": 110, "Q53.1": 111, "Q53.2": 112, "Q54.1": 113, "Q54.2": 114, "Q55.1": 115, "Q55.2": 116, "Q56.1": 117, "Q56.2": 118, "Q57.1": 119, "Q57.2": 120, "Q58.1": 121, "Q58.2": 122, "Q59.1": 123, "Q59.2": 124, "Q60.1": 125, "Q60.2": 126,
# 		"Q61.1": 127, "Q61.2": 128, "Q62.1": 129, "Q62.2": 130, "Q63.1": 131, "Q63.2": 132, "Q64.1": 133, "Q64.2": 134, "Q65.1": 135, "Q65.2": 136, "Q66.1": 137, "Q66.2": 138, "Q67.1": 139, "Q67.2": 140, "Q68.1": 141, "Q68.2": 142, "Q69.1": 143, "Q69.2": 144, "Q70.1": 145, "Q70.2": 146,
# 		"Q71.1": 147, "Q71.2": 148, "Q72.1": 149, "Q72.2": 150, "Q73.1": 151, "Q73.2": 152, "Q74.1": 153, "Q74.2": 154, "Q75.1": 155, "Q75.2": 156, "Q76.1": 157, "Q76.2": 158, "Q77.1": 159, "Q77.2": 160, "Q78.1": 161, "Q78.2": 162, "Q79.1": 163, "Q79.2": 164, "Q80.1": 165, "Q80.2": 166,
# 		"Q81.1": 167, "Q81.2": 168, "Q82.1": 169, "Q82.2": 170, "Q83.1": 171, "Q83.2": 172, "Q84.1": 173, "Q84.2": 174, "Q85.1": 175, "Q85.2": 176, "Q86": 177, "Q87": (178, 179), "Q88.1": 180, "Q88.2": 181, "Q89.1": 182, "Q89.2": 183, "Q90.1": 184, "Q90.2": 185,
# 		"Q91.1": 186, "Q91.2": 187, "Q92.1": 188, "Q92.2": 189, "Q93.1": 190, "Q93.2": 191
# 	})

# # ADOS1
# convert_phenotypes("SVIP/SVIP_1q21.1/ados_1.csv", "SVIP", "ADOS_Module1",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, 
# 		"QB01": 14, "QB02": 15, "QB03": 16, "QB04": 17, "QB05": 18, "QB06": 19, "QB07": 20, "QB08": 21, "QB09": 22, "QB10": 23, "QB11": 24, "QB12": 25, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 		"QC01": 26, "QC02": 27, 
# 		"QD01": 28, "QD02": 29, "QD03": 30, "QD04": 31, 
# 		"QE01": 32, "QE02": 33, "QE03": 34
# 	})

# # ADOS1
# convert_phenotypes("SVIP/SVIP_16p11.2/ados_1.csv", "SVIP", "ADOS_Module1",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, 
# 		"QB01": 14, "QB02": 15, "QB03": 16, "QB04": 17, "QB05": 18, "QB06": 19, "QB07": 20, "QB08": 21, "QB09": 22, "QB10": 23, "QB11": 24, "QB12": 25, "QB13.1": None, "QB13.2": None, "QB14": None, "QB15": None, "QB16": None,
# 		"QC01": 26, "QC02": 27, 
# 		"QD01": 28, "QD02": 29, "QD03": 30, "QD04": 31, 
# 		"QE01": 32, "QE02": 33, "QE03": 34
# 	})


# # ADOS2
# convert_phenotypes("SVIP/SVIP_1q21.1/ados_2.csv", "SVIP", "ADOS_Module2",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 8, "QA03": 9, "QA04": 10, "QA05": 11, "QA06": 12, "QA07": 13, 
# 		"QB01": 14, "QB02": 15, "QB03": 16, "QB04": 17, "QB05": 18, "QB06": 19, "QB07": 20, "QB08": 21, "QB09.1": None, "QB09.2": None, "QB10": 22, "QB11": 23, "QB12": 24,
# 		"QC01": 25, "QC02": 26, 
# 		"QD01": 27, "QD02": 28, "QD03": 29, "QD04": 30, 
# 		"QE01": 31, "QE02": 32, "QE03": 33
# 	})

# # ADOS2
# convert_phenotypes("SVIP/SVIP_16p11.2/ados_2.csv", "SVIP", "ADOS_Module2",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 8, "QA03": 9, "QA04": 10, "QA05": 11, "QA06": 12, "QA07": 13, 
# 		"QB01": 14, "QB02": 15, "QB03": 16, "QB04": 17, "QB05": 18, "QB06": 19, "QB07": 20, "QB08": 21, "QB09.1": None, "QB09.2": None, "QB10": 22, "QB11": 23, "QB12": 24,
# 		"QC01": 25, "QC02": 26, 
# 		"QD01": 27, "QD02": 28, "QD03": 29, "QD04": 30, 
# 		"QE01": 31, "QE02": 32, "QE03": 33
# 	})

# # ADOS3
# convert_phenotypes("SVIP/SVIP_1q21.1/ados_3.csv", "SVIP", "ADOS_Module3",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, "QA09": 14, 
# 		"QB01": 15, "QB02": 16, "QB03": 17, "QB04": 18, "QB05": 19, "QB06": 20, "QB07": 21, "QB08": None, "QB09": 22, "QB10": 23, "QB11": 24,
# 		"QC01": 25,
# 		"QD01": 26, "QD02": 27, "QD03": 28, "QD04": 29, "QD05": 30, 
# 		"QE01": 31, "QE02": 32, "QE03": 33
# 	})

# # ADOS3
# convert_phenotypes("SVIP/SVIP_16p11.2/ados_3.csv", "SVIP", "ADOS_Module3",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, "QA09": 14, 
# 		"QB01": 15, "QB02": 16, "QB03": 17, "QB04": 18, "QB05": 19, "QB06": 20, "QB07": 21, "QB08": None, "QB09": 22, "QB10": 23, "QB11": 24,
# 		"QC01": 25,
# 		"QD01": 26, "QD02": 27, "QD03": 28, "QD04": 29, "QD05": 30, 
# 		"QE01": 31, "QE02": 32, "QE03": 33
# 	})

# # ADOS4
# convert_phenotypes("SVIP/SVIP_1q21.1/ados_4.csv", "SVIP", "ADOS_Module4",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, "QA09": 14, "QA10": 15, 
# 		"QB01": 16, "QB02": 17, "QB03": 18, "QB04": 19, "QB05": 20, "QB06": 21, "QB07": 22, "QB08": 23, "QB09": 24, "QB10": None, "QB11": 25, "QB12": 26, "QB13": 27,
# 		"QC01": 28,
# 		"QD01": 29, "QD02": 30, "QD03": 31, "QD04": 32, "QD05": 33, 
# 		"QE01": 34, "QE02": 35, "QE03": 36
# 	})

# # ADOS4
# convert_phenotypes("SVIP/SVIP_16p11.2/ados_4.csv", "SVIP", "ADOS_Module4",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	},   
# 	{
# 		"QA01": 6, "QA02": 7, "QA03": 8, "QA04": 9, "QA05": 10, "QA06": 11, "QA07": 12, "QA08": 13, "QA09": 14, "QA10": 15, 
# 		"QB01": 16, "QB02": 17, "QB03": 18, "QB04": 19, "QB05": 20, "QB06": 21, "QB07": 22, "QB08": 23, "QB09": 24, "QB10": None, "QB11": 25, "QB12": 26, "QB13": 27,
# 		"QC01": 28,
# 		"QD01": 29, "QD02": 30, "QD03": 31, "QD04": 32, "QD05": 33, 
# 		"QE01": 34, "QE02": 35, "QE03": 36
# 	})

# # SRS
# convert_phenotypes("SVIP/SVIP_1q21.1/srs_parent.csv", "SVIP", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(25, 90))),
# 	value_transform=srs_transform)

# # SRS
# convert_phenotypes("SVIP/SVIP_1q21.1/srs_adult.csv", "SVIP", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(14, 79))),
# 	value_transform=srs_transform)

# # SRS
# convert_phenotypes("SVIP/SVIP_16p11.2/srs_parent.csv", "SVIP", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(25, 90))),
# 	value_transform=srs_transform)

# # SRS
# convert_phenotypes("SVIP/SVIP_16p11.2/srs_adult.csv", "SVIP", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: x[10],
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(14, 79))),
# 	value_transform=srs_transform)

# # SRS
# convert_phenotypes("SVIP/SVIP_Phase_2_1q21.1/srs_adult.csv", "SVIP", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(81, 146))))

# # SRS
# convert_phenotypes("SVIP/SVIP_Phase_2_1q21.1/srs_sa.csv", "SVIP", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(78, 143))))

# # SRS
# convert_phenotypes("SVIP/SVIP_Phase_2_16p11.2/srs_adult.csv", "SVIP", "SRS_Adult",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(81, 146))))

# # SRS
# convert_phenotypes("SVIP/SVIP_Phase_2_16p11.2/srs_sa.csv", "SVIP", "SRS_Child",
# 	{
# 		"identifier": lambda x: x[0],
# 		"gender": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][7].title(),
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[0] not in svip_demo or svip_demo[x[0]][6] == '' else int(svip_demo[x[0]][6]),
# 		"interview_date": lambda x: None,
# 		"family": lambda x: None if x[0] not in svip_demo else svip_demo[x[0]][1],
# 		"clinical_diagnosis_raw": lambda x: None if x[0] not in svip_diagnosis else svip_diagnosis[x[0]]
# 	}, 
# 	dict(zip(['Q' + str(i).zfill(2) for i in range(1, 66)], range(78, 143))))

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- AGP ------------------------------------------------------
# # *
# # ***************************************************************************************************************

# # Pull demo
# agp_demo = {}
# pheno_class_to_diag = {'1': 'Strict autism', '2': 'Broad autism', '3': 'Spectrum autism', '4': None, '*': 'Control'}
# with open(directory + "/AGP_pheno_all_201112/phase_all_pheno_class_201112/all_pheno_class_201112.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	header = next(reader)
# 	agp_demo.update([('%s-%s' % (x[1], x[2]), x) for x in reader])

# # ADIR1995
# convert_phenotypes("AGP_pheno_all_201112/adi_95_long.csv", "AGRE", "ADIR1995",
# 	{
# 		"identifier": lambda x: '%s-%s' % (x[0], x[1]),
# 		"gender": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else 'Male' if agp_demo['%s-%s' % (x[0], x[1])][5] == '1' else 'Female',
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[3] == '*' else int(x[3]),
# 		"interview_date": lambda x: x[2],
# 		"family": lambda x: x[0],
# 		"clinical_diagnosis_raw": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else pheno_class_to_diag[agp_demo['%s-%s' % (x[0], x[1])][10]]
# 	}, 
# 	{
# 	'Q002': 8, 'Q004': 13, 'Q005': 14, 'Q006': 15, 'Q007': 16, 'Q008': 17, 'Q009': 18, 'Q010': 19, 
# 	'Q011': 20, 'Q011E': 21, 'Q012': 22, 'Q013': 23, 'Q014': 24, 'Q014E': 25, 'Q015': 26, 'Q015E': 27, 'Q016': 28, 'Q016E': 29, 'Q017': 30, 'Q017E': 31, 'Q018': 32, 'Q018E': 33, 'Q019': 34, 
# 	'Q020': 35, 'Q020E': 36, 'Q021': 37, 'Q021E': 38, 'Q022': 39, 'Q022E': 40, 'Q023': 41, 'Q023E': 42, 'Q024': 43, 'Q024E': 44, 'Q025': 45, 'Q025E': 46, 'Q026': 47, 'Q026E': 48, 'Q027': 49, 'Q027E': 50, 'Q028': 51, 'Q028E': 52, 'Q029': 53, 'Q029E': 54, 'Q030': 55, 'Q030E': 56, 
# 	'Q031': 57, 'Q031E': 58, 'Q032': 59, 'Q032E': 60, 'Q033': 61, 'Q033E': 62, 'Q034': 63, 'Q034A': 65, 'Q034AE': 66, 'Q034E': 64, 'Q035E': 67, 'Q036': 68, 'Q036E': 69, 'Q037E': 70, 'Q038E': 71, 'Q039E': 72, 'Q040E': 73, 
# 	'Q041E': 74, 'Q042': 75, 'Q042E': 76, 'Q043': 77, 'Q043E': 78, 'Q044': 79, 'Q044E': 80, 'Q045': 81, 'Q045E': 82, 'Q046': 83, 'Q046E': 84, 'Q047': 85, 'Q047E': 86, 'Q048': 87, 'Q048E': 88, 'Q049': 89, 'Q049E': 90, 'Q050': 91, 'Q050E': 92, 
# 	'Q051': 93, 'Q051E': 94, 'Q052': 95, 'Q052E': 96, 'Q053': 97, 'Q053E': 98, 'Q054': 99, 'Q054E': 100, 'Q055': 101, 'Q055E': 102, 'Q056': 103, 'Q056E': 104, 'Q057': 105, 'Q057E': 106, 'Q058': 107, 'Q058E': 108, 'Q059': 109, 'Q059E': 110, 'Q060': 111, 'Q060E': 112,
# 	'Q061': 113, 'Q061E': 114, 'Q062': 115, 'Q062E': 116, 'Q063': 117, 'Q063E': 118, 'Q064': 119, 'Q064E': 120, 'Q065': 121, 'Q065E': 122, 'Q066': 123, 'Q066E': 124, 'Q067': 125, 'Q067E': 126, 'Q068': 127, 'Q068E': 128, 'Q069': 129, 'Q069E': 130, 'Q070': 131, 'Q070E': 132, 
# 	'Q071': 133, 'Q071E': 134, 'Q072': 135, 'Q072E': 136, 'Q073': 137, 'Q073E': 138, 'Q074': 139, 'Q074E': 140, 'Q075': 141, 'Q075E': 142, 'Q076': 143, 'Q076E': 144, 'Q077': 145, 'Q077E': 146, 'Q078': 147, 'Q078E': 148, 'Q079': 149, 'Q079E': 150, 'Q080': 151, 'Q080E': 152, 
# 	'Q081': 153, 'Q081E': 154, 'Q082': 155, 'Q082E': 156, 'Q083': 157, 'Q083E': 158, 'Q084': 159, 'Q084E': 160, 'Q085': 161, 'Q085E': 162, 'Q086': 163, 'Q086E': 164, 'Q087': 165, 'Q088': 166, 'Q088E': 167, 'Q089': 168, 'Q089E': 169, 'Q090': 170, 'Q090E': 171, 
# 	'Q091': 172, 'Q091E': 173, 'Q091.2': None, 'Q091.2E': None, 'Q091.3': None, 'Q091.3E': None, 'Q092': 174, 'Q092E': 175, 'Q093': 176, 'Q094': 177, 'Q095A5': 179, 'Q095B5': 178, 'Q096A5': 181, 'Q096B5': 180, 'Q097A5': 183, 'Q097B5': 182, 'Q098A5': 185, 'Q098B5': 184, 'Q099A5': 187, 'Q099B5': 186, 'Q100A5': 189, 'Q100B5': 188, 
# 	'Q101A5': 191, 'Q101B5': 190, 'Q102A5': 193, 'Q102B5': 192, 'Q103': 194, 'Q104': 195, 'Q105': 196, 'Q106': 197, 'Q106E': 198, 'Q107': 199, 'Q107E': 200, 'Q108': 201, 'Q108E': 202, 'Q109': 203, 'Q109E': 204, 'Q110': 205, 'Q110E': 206, 'Q111': 207, 'Q111E': 208
# 	})

# # ADIR1995
# #print_codes_for_instrument('ADIR1995_Short')
# convert_phenotypes("AGP_pheno_all_201112/adi_95_short.csv", "AGRE", "ADIR1995",
# 	{
# 		"identifier": lambda x: '%s-%s' % (x[0], x[1]),
# 		"gender": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else 'Male' if agp_demo['%s-%s' % (x[0], x[1])][5] == '1' else 'Female',
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[3] == '*' else int(x[3]),
# 		"interview_date": lambda x: x[2],
# 		"family": lambda x: x[0],
# 		"clinical_diagnosis_raw": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else pheno_class_to_diag[agp_demo['%s-%s' % (x[0], x[1])][10]]
# 	}, 
# 	adir_short_to_long({'Q02': 8, 'Q04': 13, 'Q05': 14, 'Q06': 15, 'Q07': 16, 'Q07E': 17, 'Q08': 18, 'Q09': 19, 
# 		'Q10': 20, 'Q10E': 21, 'Q11': 22, 'Q11E': 23, 'Q12': 24, 'Q12E': 25, 'Q13': 26, 'Q13E': 27, 'Q14': 28, 'Q15': 29, 'Q15E': 30, 'Q16': 31, 'Q16E': 32, 'Q17': 33, 'Q17E': 34, 'Q18': 35, 'Q18E': 36, 'Q19': 37, 'Q19E': 38, 
# 		'Q20': 39, 'Q20E': 40, 'Q21': 41, 'Q21E': 42, 'Q22': 43, 'Q22E': 44, 'Q23': 45, 'Q23E': 46, 'Q24': 47, 'Q24E': 48, 'Q25': 49, 'Q25E': 50, 'Q26': 51, 'Q26E': 52, 'Q27E': 53, 'Q28': 54, 'Q28E': 55, 'Q29': 56, 'Q29E': 57, 
# 		'Q30': 58, 'Q30E': 59, 'Q31': 60, 'Q31E': 61, 'Q32': 62, 'Q32E': 63, 'Q33': 64, 'Q33E': 65, 'Q34': 66, 'Q34E': 67, 'Q35': 68, 'Q35E': 69, 'Q36': 70, 'Q36E': 71, 'Q37': 72, 'Q37E': 73, 'Q38': 74, 'Q38E': 75, 'Q39': 76, 'Q39E': 77, 
# 		'Q40': 78, 'Q40E': 79, 'Q41': 80, 'Q41E': 81, 'Q42': 82, 'Q42E': 83, 'Q43': 84, 'Q43E': 85, 'Q44': 86, 'Q44E': 87, 'Q45': 88, 'Q45E': 89, 'Q46': 90, 'Q46E': 91, 'Q47': 92, 'Q47E': 93, 'Q48': 94, 'Q48E': 95, 'Q49': 96, 'Q49E': 97, 
# 		'Q50': 98, 'Q50E': 99, 'Q51': 100, 'Q51E': 101, 'Q52': 102, 'Q52E': 103, 'Q53': 104, 'Q53E': 105, 'Q54': 106, 'Q54E': 107, 'Q55': 108, 'Q56': 109, 'Q57': 110, 'Q57E': 111, 'Q58': 112, 'Q58E': 113, 'Q59': 114, 'Q59E': 115, 
# 		'Q60': 116, 'Q60E': 117, 'Q61': 118, 'Q61E': 119, 'Q62': 120, 'Q62E': 121
# 	}))

# # ADIR2003
# convert_phenotypes("AGP_pheno_all_201112/adi_wps.csv", "AGRE", "ADIR2003",
# 	{
# 		"identifier": lambda x: '%s-%s' % (x[0], x[1]),
# 		"gender": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else 'Male' if agp_demo['%s-%s' % (x[0], x[1])][5] == '1' else 'Female',
# 		"race": lambda x: None,
# 		"ethnicity": lambda x: None,
# 		"age": lambda x: None if x[3] == '*' else int(x[3]),
# 		"interview_date": lambda x: x[2],
# 		"family": lambda x: x[0],
# 		"clinical_diagnosis_raw": lambda x: None if '%s-%s' % (x[0], x[1]) not in agp_demo else pheno_class_to_diag[agp_demo['%s-%s' % (x[0], x[1])][10]]
# 	}, 
# 	{
#  		"Q02": 4, "Q04": 5, "Q05": 6, "Q06": 7, "Q07": 8, "Q08": 9, "Q09": 10, "Q10": 11,
#  		"Q11": 12, "Q12": 13, "Q13": 14, "Q14": 15, "Q15": 16, "Q16": 17, "Q17": 18, "Q18": 19, "Q19": 20, "Q20": 21,
# 		"Q21": 22, "Q22": 23, "Q23": 24, "Q24": 25, "Q25": 26, "Q26": 27, "Q27": 28, "Q28": 29, "Q29.1": 30, "Q29.2": 31, "Q30": 32,
# 		"Q31.1": 33, "Q31.2": 34, "Q32.1": 35, "Q32.2": 36, "Q33.1": 37, "Q33.2": 38, "Q34.1": 39, "Q34.2": 40, "Q35.1": 41, "Q35.2": 42, "Q36.1": 43, "Q36.2": 44, "Q37.1": 45, "Q37.2": 46, "Q38.1": 47, "Q38.2": 48, "Q39.1": 49, "Q39.2": 50, "Q40.1": 51, "Q40.2": 52,
# 		"Q41.1": 53, "Q41.2": 54, "Q42.1": 55, "Q42.2": 56, "Q43.1": 57, "Q43.2": 58, "Q44.1": 59, "Q44.2": 60, "Q45.1": 61, "Q45.2": 62, "Q46.1": 63, "Q46.2": 64, "Q47.1": 65, "Q47.2": 66, "Q48.1": 67, "Q48.2": 68, "Q49.1": 69, "Q49.2": 70, "Q50.1": 71, "Q50.2": 72,
# 		"Q51.1": 73, "Q51.2": 74, "Q52.1": 75, "Q52.2": 76, "Q53.1": 77, "Q53.2": 78, "Q54.1": 79, "Q54.2": 80, "Q55.1": 81, "Q55.2": 82, "Q56.1": 83, "Q56.2": 84, "Q57.1": 85, "Q57.2": 86, "Q58.1": 87, "Q58.2": 88, "Q59.1": 89, "Q59.2": 90, "Q60.1": 91, "Q60.2": 92,
# 		"Q61.1": 93, "Q61.2": 94, "Q62.1": 95, "Q62.2": 96, "Q63.1": 97, "Q63.2": 98, "Q64.1": 99, "Q64.2": 100, "Q65.1": 101, "Q65.2": 102, "Q66.1": 103, "Q66.2": 104, "Q67.1": 105, "Q67.2": 106, "Q68.1": 107, "Q68.2": 108, "Q69.1": 109, "Q69.2": 110, "Q70.1": 111, "Q70.2": 112,
# 		"Q71.1": 113, "Q71.2": 114, "Q72.1": 115, "Q72.2": 116, "Q73.1": 117, "Q73.2": 118, "Q74.1": 119, "Q74.2": 120, "Q75.1": 121, "Q75.2": 122, "Q76.1": 123, "Q76.2": 124, "Q77.1": 125, "Q77.2": 126, "Q78.1": 127, "Q78.2": 128, "Q79.1": 129, "Q79.2": 130, "Q80.1": 131, "Q80.2": 132,
# 		"Q81.1": 133, "Q81.2": 134, "Q82.1": 135, "Q82.2": 136, "Q83.1": 137, "Q83.2": 138, "Q84.1": 139, "Q84.2": 140, "Q85.1": 141, "Q85.2": 142, "Q86": 143, "Q87": 144, "Q88.1": 145, "Q88.2": 146, "Q89.1": 147, "Q89.2": 148, "Q90.1": 149, "Q90.2": 150,
# 		"Q91.1": 151, "Q91.2": 152, "Q92.1": 153, "Q92.2": 154, "Q93.1": 155, "Q93.2": 156
# 	})

# # ***************************************************************************************************************
# # *
# # --------------------------------------------------- MSSNG ------------------------------------------------------
# # *
# # ***************************************************************************************************************

mssng_sex = {}
with open(directory + '/mssng/tanner.csv') as f:
	for line in f:
		pieces = line.strip().split(',')

		sex = None
		if pieces[2] == '1':
			sex = 'Male'
		elif pieces[2] == '2':
			sex = 'Female'
		elif pieces[5] != '':
			sex = 'Female'
		elif pieces[10] != '':
			sex = 'Male'

		if sex is not None:
			mssng_sex[pieces[0]] = sex
		else:
			print('Sex not found', pieces[0])

# ADIR1995
# print_codes_for_instrument('ADIR1995')
convert_phenotypes("mssng/adi1995.csv", "MSSNG", "ADIR1995",
	{
		"identifier": lambda x: x[0],
		"gender": lambda x: None if x[0] not in mssng_sex else mssng_sex[x[0]],
		"race": lambda x: None,
		"ethnicity": lambda x: None,
		"age": lambda x: int(round(12*float(x[12]), 0)),
		"interview_date": lambda x: x[1],
		"family": lambda x: x[7],
		"clinical_diagnosis_raw": lambda x: None if x[6] not in agre_diagnosis else agre_diagnosis[x[6]]
	}, 
	{
	'Q002': 130, 'Q004': 136, 'Q005': 140, 'Q006', 'Q007', 'Q008', 'Q009', 
	'Q010': 193, 'Q011': 194, 'Q011E': 14, 'Q012': 195, 'Q013': 199, 'Q014': 202, 'Q014E': 177, 'Q015': 203, 'Q015E': 32, 'Q016': 206, 'Q016E': 186, 'Q017': 210, 'Q017E': 44, 'Q018': 212, 'Q018E': 201, 'Q019': 214, 
	'Q020': 49, 'Q020E': 200, 'Q021': 51, 'Q021E': 57, 'Q022': 52, 'Q022E': 219, 'Q023': 55, 'Q023E': 75, 'Q024': 56, 'Q024E': 241, 'Q025': 58, 'Q025E': 102, 'Q026': 62, 'Q026E': 271, 'Q027': 65, 'Q027E': 127, 'Q028': 68, 'Q028E': 292, 'Q029'70, 'Q029E': 148, 
	'Q030': 208, 'Q030E': 291, 'Q031': 211, 'Q031E': 147, 'Q032': 213, 'Q032E': 4, 'Q033': 217, 'Q033E': 162, 'Q034': 218, 'Q034A': 11, 'Q034AE': 77, 'Q034E': 21, 'Q035E': 174, 'Q036': 224, 'Q036E': 28, 'Q037E': 181, 'Q038E': 38, 'Q039E': 190, 
	'Q040E': 37, 'Q041E': 189, 'Q042': 69, 'Q042E': 48, 'Q043': 73, 'Q043E': 207, 'Q044': 74, 'Q044E': 64, 'Q045': 76, 'Q045E': 227, 'Q046': 81, 'Q046E': 85, 'Q047': 84, 'Q047E': 251, 'Q048': 90, 'Q048E': 111, 'Q049': 93, 'Q049E': 281, 
	'Q050': 226, 'Q050E', 'Q051', 'Q051E', 'Q052', 'Q052E', 'Q053', 'Q053E', 'Q054', 'Q054E', 'Q055', 'Q055E', 'Q056', 'Q056E', 'Q057', 'Q057E', 'Q058', 'Q058E', 'Q059', 'Q059E', 
	'Q060', 'Q060E', 'Q061', 'Q061E', 'Q062', 'Q062E', 'Q063', 'Q063E', 'Q064', 'Q064E', 'Q065', 'Q065E', 'Q066', 'Q066E', 'Q067', 'Q067E', 'Q068', 'Q068E', 'Q069', 'Q069E', 
	'Q070', 'Q070E', 'Q071', 'Q071E', 'Q072', 'Q072E', 'Q073', 'Q073E', 'Q074', 'Q074E', 'Q075', 'Q075E', 'Q076', 'Q076E': 3, 'Q077', 'Q077E', 'Q078', 'Q078E', 'Q079', 'Q079E', 
	'Q080', 'Q080E', 'Q081', 'Q081E', 'Q082', 'Q082E', 'Q083', 'Q083E', 'Q084', 'Q084E', 'Q085', 'Q085E', 'Q086', 'Q086E', 'Q087', 'Q088', 'Q088E', 'Q089', 'Q089E', 
	'Q090', 'Q090E', 'Q091', 'Q091E', 'Q091.2', 'Q091.2E', 'Q091.3', 'Q091.3E', 'Q092', 'Q092E', 'Q093', 'Q094', 'Q095A5', 'Q095B5', 'Q096A5', 'Q096B5', 'Q097A5', 'Q097B5', 'Q098A5', 'Q098B5', 'Q099A5', 'Q099B5', 
	'Q100A5': 20, 'Q100B5': 173, 'Q101A5': 63, 'Q101B5': 225, 'Q102A5': 152, 'Q102B5': 8, 'Q103': 103, 'Q104': 105, 'Q105': 107, 'Q106': 112, 'Q106E': 293, 'Q107': 115, 'Q107E': 151, 'Q108': 118, 'Q108E': 6, 'Q109': 123, 'Q109E': 166, 'Q110': 255, 'Q110E': 7, 'Q111': 258, 'Q111E': 267
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


