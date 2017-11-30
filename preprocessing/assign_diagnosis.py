import json
import jsonschema
import sys
from collections import defaultdict

# This script assigns a variety of diagnoses to each individual in the aggregated phenotype dataset.

# Instrument diagnoses - each instrument is assigned a diagnosis based on item-level data using the 
# diagnostic instructions provided for each instrument.

# ADOS diagnosis - the aggregated ADOS instrument is assigned a diagnosis of Autism if any ADOS module
# diagnosed autism for this individual. Otherwise, it is assigned a diagnosis of Autism Spectrum if
# and ADOS module diagnosed autism spectrum. Otherwise Control if any module diagnosed control. Otherwise None.

# CPEA diagnosis - a CPEA diagnosis is assigned as best as possible based on CPEA criteria, although
# some cirteria were ignored if we didn't have the data (ex. IQ)

# Overall diagnosis - the top level diagnosis field is currently set to be Autism if any instrument or
# CPEA diagnoses autism or autism spectrum. Otherwise control if any instrument diagnoses control. Otherwise None.

# This code requires aggregate_phenotype.py and aggregate_ados.py to already have been run.
# It outputs a file called all_samples.json which contains diagnoses for all instruments.
# It is meant to be run as part of a multi-stage pipeline described in the README.

# The code can be run with:
# python3 assign_diagnosis.py

def calculate_subscore(score_name, sample, instrument, features, additional_score_entries = [], calculate_score_f = lambda score_entries: sum([2 if x==3 else (0 if x>3 else x) for x in score_entries if x is not None])):
	score_entries = [sample[instrument][feature] for feature in features]
	score_entries.extend(additional_score_entries)
	sample[instrument][score_name] = calculate_score_f(score_entries)
	num_nulls = sum(x is None for x in score_entries)
	return num_nulls

def assign_adir_diagnosis(sample):
	instrument = 'ADIR'
	if instrument in sample:

		# Social interacton
		a_num_nulls = 0
		a_num_nulls += calculate_subscore('A1', sample, instrument, ['Q50.2', 'Q51.2', 'Q57.2'])
		a_num_nulls += calculate_subscore('A2', sample, instrument, ['Q49.2', 'Q62.2', 'Q63.2'], 
			additional_score_entries=[sample[instrument]['Q64.2'] if (sample[instrument]['age'] is None or sample[instrument]['age'] < 120) else sample[instrument]['Q65.2']])
		a_num_nulls += calculate_subscore('A3', sample, instrument, ['Q52.2', 'Q53.2', 'Q54.2'])
		a_num_nulls += calculate_subscore('A4', sample, instrument, ['Q31.2', 'Q55.2', 'Q56.2', 'Q58.2', 'Q59.2'])

		calculate_subscore('social_interaction', sample, instrument, 
			['A1', 'A2', 'A3', 'A4'], calculate_score_f=lambda score_entries: sum([x for x in score_entries if x is not None]))

		# Communication
		is_verbal = None if sample[instrument]['Q30'] is None else (sample[instrument]['Q30'] == 0)

		b_num_nulls = 0
		b_num_nulls += calculate_subscore('B1', sample, instrument, ['Q42.2', 'Q43.2', 'Q44.2', 'Q45.2'])
		b_num_nulls += calculate_subscore('B4', sample, instrument, ['Q47.2', 'Q68.2', 'Q61.2'])

		if is_verbal is not None and is_verbal:
			# If individual is verbal
			b_num_nulls += calculate_subscore('B2', sample, instrument, ['Q34.2', 'Q35.2'])
			b_num_nulls += calculate_subscore('B3', sample, instrument, ['Q33.2', 'Q36.2', 'Q37.2', 'Q37.2', 'Q38.2'])


		calculate_subscore('communication', sample, instrument, 
			['B1', 'B2', 'B3', 'B4'], calculate_score_f=lambda score_entries: sum([x for x in score_entries if x is not None]))

		# Restricted repetitive behavior
		c_num_nulls = 0
		c_num_nulls += calculate_subscore('C1', sample, instrument, ['Q67.2', 'Q68.2'])
		c_num_nulls += calculate_subscore('C2', sample, instrument, ['Q70.2'],
			additional_score_entries=[(sample[instrument]['Q39.2'] if is_verbal else 0)])
		c_num_nulls += calculate_subscore('C3', sample, instrument, [],
			additional_score_entries=[(sample[instrument]['Q77.2'] if sample[instrument]['Q78.2'] is None else (sample[instrument]['Q78.2'] if sample[instrument]['Q77.2'] is None else max(sample[instrument]['Q77.2'], sample[instrument]['Q78.2'])))])
		c_num_nulls += calculate_subscore('C4', sample, instrument, [],
			additional_score_entries=[(sample[instrument]['Q69.2'] if sample[instrument]['Q71.2'] is None else (sample[instrument]['Q71.2'] if sample[instrument]['Q69.2'] is None else max(sample[instrument]['Q69.2'], sample[instrument]['Q71.2'])))])

		calculate_subscore('restricted_repetitive_behavior', sample, instrument, 
			['C1', 'C2', 'C3', 'C4'], calculate_score_f=lambda score_entries: sum([x for x in score_entries if x is not None]))

		# Abnormality evident before 3 years
		d_num_nulls = calculate_subscore('abnormality_evident_before_3_years', sample, instrument, 
			['Q02', 'Q09', 'Q10', 'Q86', 'Q87'], 
			calculate_score_f=lambda score_entries: sum([
				(1 if score_entries[0] is not None and score_entries[0] < 36 else 0), 
				(1 if score_entries[1] is not None and score_entries[1] > 24 else 0), 
				(1 if score_entries[2] is not None and score_entries[2] > 33 else 0), 
				(1 if score_entries[3] is not None and (score_entries[3] == 3 or score_entries[3] == 4) else 0), 
				(1 if score_entries[4] is not None and score_entries[4] < 36 else 0)
			]))

		if (sample[instrument]['social_interaction'] >= 10) \
			and (((is_verbal is None or is_verbal) and sample[instrument]['communication'] >= 8) or (not is_verbal and sample[instrument]['communication'] >= 7)) \
			and (sample[instrument]['restricted_repetitive_behavior'] >= 3) \
			and (sample[instrument]['abnormality_evident_before_3_years'] >= 1):
			sample[instrument]['diagnosis'] = 'Autism'
		else:
			sample[instrument]['diagnosis'] = 'Control'
		sample[instrument]['diagnosis_num_nulls'] = a_num_nulls + b_num_nulls + c_num_nulls + d_num_nulls + (1 if is_verbal is None else 0)


def assign_ados1_diagnosis(sample):
	instrument = 'ADOS_Module1'
	if instrument in sample:

		a_num_nulls = calculate_subscore('communication', sample, instrument,  
			['QA02', 'QA07', 'QA08'])
		
		b_num_nulls = calculate_subscore('social_interaction', sample, instrument,  
			['QB01', 'QB03', 'QB04', 'QB05', 'QB09', 'QB10', 'QB11', 'QB12'])

		c_num_nulls = calculate_subscore('restricted_repetitive_behavior', sample, instrument,  
			['QA03', 'QA05', 'QD01', 'QD02', 'QD04'])

		has_words = sample[instrument]['QA01']
		score = sample[instrument]['communication'] + sample[instrument]['social_interaction'] + sample[instrument]['restricted_repetitive_behavior']
		if has_words is None or has_words >= 3:
			sample[instrument]['diagnosis'] = 'Autism' if score >= 16 else ('Autism Spectrum' if score >= 11 else 'Control')
		else:
			sample[instrument]['diagnosis'] = 'Autism' if score >= 12 else ('Autism Spectrum' if score >= 8 else 'Control')
		sample[instrument]['diagnosis_num_nulls'] = a_num_nulls + b_num_nulls + c_num_nulls + (1 if has_words is None else 0)


def assign_ados2_diagnosis(sample):
	instrument = 'ADOS_Module2'
	if instrument in sample:

		a_num_nulls = calculate_subscore('communication', sample, instrument,  
			['QA06', 'QA07'])

		b_num_nulls = calculate_subscore('social_interaction', sample, instrument,
			['QB01', 'QB02', 'QB03', 'QB05', 'QB06', 'QB08', 'QB11', 'QB12'])

		c_num_nulls = calculate_subscore('restricted_repetitive_behavior', sample, instrument,
			['QA04', 'QD01', 'QD02', 'QD04'])

		age = sample[instrument]['age']

		score = sample[instrument]['communication'] + sample[instrument]['social_interaction'] + sample[instrument]['restricted_repetitive_behavior']		
		if age is not None and age >= 60:
			sample[instrument]['diagnosis'] = 'Autism' if score >= 9 else ('Autism Spectrum' if score >= 8 else 'Control')
		else:
			sample[instrument]['diagnosis'] = 'Autism' if score >= 10 else ('Autism Spectrum' if score >= 7 else 'Control')
		sample[instrument]['diagnosis_num_nulls'] = a_num_nulls + b_num_nulls + c_num_nulls + (1 if age is None else 0)

def assign_ados3_diagnosis(sample):
	instrument = 'ADOS_Module3'
	if instrument in sample:

		a_num_nulls = calculate_subscore('communication', sample, instrument,  
			['QA07', 'QA08', 'QA09'])

		b_num_nulls = calculate_subscore('social_interaction', sample, instrument,
			['QB01', 'QB02', 'QB04', 'QB07', 'QB09', 'QB10', 'QB11'])
		
		c_num_nulls = calculate_subscore('restricted_repetitive_behavior', sample, instrument,
			['QA04', 'QD01', 'QD02', 'QD04'])

		score = sample[instrument]['communication'] + sample[instrument]['social_interaction'] + sample[instrument]['restricted_repetitive_behavior']		
		sample[instrument]['diagnosis'] = 'Autism' if score >= 9 else ('Autism Spectrum' if score >= 7 else 'Control')
		sample[instrument]['diagnosis_num_nulls'] = a_num_nulls + b_num_nulls + c_num_nulls

def assign_ados4_diagnosis(sample):
	instrument = 'ADOS_Module4'
	if instrument in sample:

		a_num_nulls = calculate_subscore('communication', sample, instrument,  
			['QA04', 'QA08', 'QA09', 'QA10'])

		b_num_nulls = calculate_subscore('social_interaction', sample, instrument,  
			['QB01', 'QB02', 'QB06', 'QB08', 'QB09', 'QB11', 'QB12'])

		c_num_nulls = calculate_subscore('restricted_repetitive_behavior', sample, instrument,
			['QD01', 'QD02', 'QD04', 'QD05'])
		
		if sample[instrument]['communication'] >= 3 and sample[instrument]['social_interaction'] >= 6 and sample[instrument]['communication'] + sample[instrument]['social_interaction'] >= 10:
			sample[instrument]['diagnosis'] = 'Autism'
		elif sample[instrument]['communication'] >= 2 and sample[instrument]['social_interaction'] >= 4 and sample[instrument]['communication'] + sample[instrument]['social_interaction'] >= 7:
			sample[instrument]['diagnosis'] = 'Autism Spectrum'
		else:
			sample[instrument]['diagnosis'] = 'Control'
		sample[instrument]['diagnosis_num_nulls'] = a_num_nulls + b_num_nulls + c_num_nulls


def assign_ados_diagnosis(sample):
	if 'ADOS' in sample:
		module = sample['ADOS']['module']
		for feature in ('diagnosis', 'diagnosis_num_nulls', 'communication', 'social_interaction', 'restricted_repetitive_behavior'):
			sample['ADOS'][feature] = sample[module][feature]


def assign_cpea_diagnosis(sample):
	if 'ADIR' in sample and 'ADOS' in sample:
		adir_diagnosis = sample['ADIR']['diagnosis']
		ados_diagnosis = sample['ADOS']['diagnosis']

		first_words = sample['ADIR']['Q09']
		first_phrases = sample['ADIR']['Q10']

		adir_soc_score = sample['ADIR']['social_interaction']
		adir_com_score = sample['ADIR']['communication']
		adir_rep_score = sample['ADIR']['restricted_repetitive_behavior']

		ados_soc_com = sample['ADOS']['social_interaction'] + sample['ADOS']['communication']

		is_verbal = None if sample['ADIR']['Q30'] is None else (sample['ADIR']['Q30'] == 0)

		if adir_diagnosis == 'Autism' and ados_diagnosis in ('Autism', 'Autism Spectrum'):
			# Also needs BEC diagnosis of Autism, Autism Spectrum or Aspergers
			sample['cpea_diagnosis'] = 'Autism'
		elif (first_words is None or first_words <= 24) and (first_phrases is None or first_phrases <= 33) and adir_diagnosis != 'Autism' \
			and adir_soc_score >= 10 and adir_rep_score >= 2 \
			and (ados_diagnosis in ('Autism', 'Autism Spectrum') or ados_soc_com >= 4):
			# Also needs age > 5, IQ > 80, BEC of Autism, Autism Spectrum or Aspergers
			sample['cpea_diagnosis'] = 'Aspergers'
		elif ((adir_soc_score >= 10 and ((is_verbal is not None and not is_verbal and adir_com_score >= 7) or adir_com_score >= 8)) \
			or (adir_soc_score >= 10 and ((is_verbal is not None and not is_verbal and adir_com_score >= 5) or adir_com_score >= 6)) \
			or (adir_soc_score >= 8 and ((is_verbal is not None and not is_verbal and adir_com_score >= 7) or adir_com_score >= 8)) \
			or (adir_soc_score >= 9 and ((is_verbal is not None and not is_verbal and adir_com_score >= 6) or adir_com_score >= 7))) \
			and ados_diagnosis == 'Autism Spectrum':
			# Also needs BEC of Autism, Autism Spectrum, or Aspergers
			sample['cpea_diagnosis'] = 'Autism Spectrum'
		else:
			sample['cpea_diagnosis'] = 'Control'


def assign_cpea_adjusted_diagnosis(sample):
	if 'ADIR' in sample and 'ADOS' in sample:
		cpea_diagnosis = sample['cpea_diagnosis']

		sample['cpea_adjusted_diagnosis'] = cpea_diagnosis
		if cpea_diagnosis == 'Control':
			adir_diagnosis = sample['ADIR']['diagnosis']
			ados_diagnosis = sample['ADOS']['diagnosis']

			if adir_diagnosis == 'Control' and ados_diagnosis == 'Control':
				sample['cpea_adjusted_diagnosis'] = 'Control'
			else:
				sample['cpea_adjusted_diagnosis'] = 'Suspected Control'
	else:
		sample['cpea_adjusted_diagnosis'] = None


def assign_diagnosis(sample):
	diags = (
		(None if 'ADIR' not in sample else sample['ADIR']['diagnosis']),
		(None if 'ADOS_Module1' not in sample else sample['ADOS_Module1']['diagnosis']),
		(None if 'ADOS_Module2' not in sample else sample['ADOS_Module2']['diagnosis']),
		(None if 'ADOS_Module3' not in sample else sample['ADOS_Module3']['diagnosis']),
		(None if 'ADOS_Module4' not in sample else sample['ADOS_Module4']['diagnosis']),
		(None if 'ADOS' not in sample else sample['ADOS']['diagnosis']),
		sample['cpea_diagnosis'])
	if 'Autism' in diags or 'Autism Spectrum' in diags or 'Aspergers' in diags:
		sample['diagnosis'] = 'Autism'
	elif 'Control' in diags:
		sample['diagnosis'] = 'Control'
	else:
		sample['diagnosis'] = None

def assign_clinical_diagnosis(sample):
	if sample['clinical_diagnosis_raw'] is not None:
		cd = sample['clinical_diagnosis_raw'].lower()
		if cd == '':
			sample['clinical_diagnosis'] = None
		elif 'aut' in cd or '299' in cd or cd in ['proband', 'broadspectrum', 'asd', 'affected sibling', 'ad']:
			sample['clinical_diagnosis'] = 'Autism'
		elif 'asperger' in cd:
			sample['clinical_diagnosis'] =  'Asperger'
		elif cd in ['nqa', 'not met', 'control']:
			sample['clinical_diagnosis'] =  'Control'
		elif 'pdd' in cd or 'nos' in cd or 'pervasive developmental disorder' in cd:
			sample['clinical_diagnosis'] = 'PDD-NOS'
		elif 'not' in cd:
			print(sample['dataset'], sample['identifier'], cd)
		else:
			print(sample['dataset'], sample['identifier'], cd)

def assign_all_diagnoses(sample):
	assign_adir_diagnosis(sample)

	assign_ados1_diagnosis(sample)
	assign_ados2_diagnosis(sample)
	assign_ados3_diagnosis(sample)
	assign_ados4_diagnosis(sample)
	assign_ados_diagnosis(sample)

	assign_cpea_diagnosis(sample)
	assign_cpea_adjusted_diagnosis(sample)

	assign_diagnosis(sample)
	assign_clinical_diagnosis(sample)

from collections import Counter
if __name__ == '__main__':
	# Load schema
	with open("AutismPhenotype.json") as schema_file:    
		pheno_schema = json.load(schema_file)

	with open(sys.argv[1], 'r') as infile:

		# Read in samples
		samples = json.load(infile)

		# Diagnose
		for sample in samples:
			# Assign diagnoses
			assign_all_diagnoses(sample)

			# Validate schema
			#jsonschema.validate(sample, pheno_schema)

		# Print counts
		diag_keys = ['clinical_diagnosis_raw', 'clinical_diagnosis', 'diagnosis',
		'cpea_diagnosis', 'cpea_adjusted_diagnosis']

		for key in diag_keys:
			print(key)
			print(Counter([s[key] for s in samples]))

		# Write to file
		with open(sys.argv[2], 'w+') as outfile:
			json.dump(samples, outfile, sort_keys=True, indent=4)

		

		

