import csv
import json
import sys

# This script column filters all_samples.csv
# We are discarding the following features for analysis:
# "Medical History" related features
# ADOS Modules (we keep the aggregated ADOS instrument instead)
# Categorical features - these features correspond to the 9** codes in ADIR and ADOS - they generally mean "unknown" and are not useful for our analysis

# This code requires an all_samples.csv file to filter.
# It outputs a file called all_samples_filtred.csv which contains our features of interest
# It is meant to be run as part of a multi-stage pipeline described in the README.

# The code can be run with:
# python3 filter_ordinal_features.py

filename = sys.argv[1]

with open("schemas/Individual.json") as schema_file:    
	pheno_schema = json.load(schema_file)

ordinal_features = set()
for instrument in [k for k, v in pheno_schema['properties'].items() if 'type' in v and v['type'] == 'object']:
	with open('schemas/%s.json' % instrument) as instrument_schema_file:
		instrument_schema = json.load(instrument_schema_file)
		for feature in instrument_schema['properties'].keys():
			if 'data-type' in instrument_schema['properties'][feature] and instrument_schema['properties'][feature]['data-type'] == 'ordinal':
				ordinal_features.add('%s:%s' % (instrument, feature))

# # Accumulate missing data counts for rows and columns
# with open(filename + '.csv', 'r') as infile:
# 	reader = csv.reader(infile)
# 	col_null_counts = [0.0]*len(next(reader))
# 	row_null_counts = []

# 	for row in reader:
# 		c = 0
# 		for j, e in enumerate(row):
# 			if e == '' or e == 'None':
# 				col_null_counts[j] += 1
# 				c += 1
# 		row_null_counts.append(c)

# col_null_counts = [x/len(row_null_counts) for x in col_null_counts]
# row_null_counts = [x/len(col_null_counts) for x in row_null_counts]

# Pull ordinal features
with open(filename + '.csv', 'r') as infile:
	reader = csv.reader(infile)
	header = next(reader)

	label_cols = ['identifier', 'clinical_diagnosis', 'gender', 'dataset', 'age', 'race', 'ethnicity', 
		'family', 'mother_id', 'father_id',
		'ADIR2003:diagnosis', 'ADIR2003:diagnosis_num_nulls',
		'ADOS_Module1:diagnosis', 'ADOS_Module1:diagnosis_num_nulls', 
		'ADOS_Module2:diagnosis', 'ADOS_Module2:diagnosis_num_nulls', 
		'ADOS_Module3:diagnosis', 'ADOS_Module3:diagnosis_num_nulls', 
		'ADOS_Module4:diagnosis', 'ADOS_Module4:diagnosis_num_nulls', 
		'ADOS2_Module1:diagnosis', 'ADOS2_Module1:diagnosis_num_nulls', 
		'ADOS2_Module2:diagnosis', 'ADOS2_Module2:diagnosis_num_nulls', 
		'ADOS2_Module3:diagnosis', 'ADOS2_Module3:diagnosis_num_nulls', 
		'ADOS2_Module4:diagnosis', 'ADOS2_Module4:diagnosis_num_nulls', 
		'SRS_Child:diagnosis', 'SRS_Child:diagnosis_num_nulls'
	]
	label_cols = [x for x in label_cols if x in header]
	label_indices = [header.index(x) for x in label_cols]

	keep_cols = [header.index('identifier')]

	# Pull ordinal features
	for i, h in enumerate(header):
		#if col_null_counts[i] <= 1: #.4:
		if h in ordinal_features:
			keep_cols.append(i)

	print('Keeping %d features' % (len(keep_cols)-1))

	with open(filename + '_ordinal_labels.csv', 'w+') as label_outfile:
		with open(filename + '_ordinal.csv', 'w+') as outfile:
			label_writer = csv.writer(label_outfile)
			writer = csv.writer(outfile)

			label_writer.writerow(label_cols)
			writer.writerow([header[i] for i in keep_cols])
			for i, row in enumerate(reader):
				#if row_null_counts[i] <= 1: #.6:
				label_writer.writerow([("None" if row[i] == '' else row[i]) for i in label_indices])
				writer.writerow([("None" if row[i] == '' else row[i]) for i in keep_cols])


