import csv
import json
import sys
import numpy as np

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
instruments = [k for k, v in pheno_schema['properties'].items() if 'type' in v and v['type'] == 'object']
for instrument in instruments:
	with open('schemas/%s.json' % instrument) as instrument_schema_file:
		instrument_schema = json.load(instrument_schema_file)
		for feature in instrument_schema['properties'].keys():
			if 'data-type' in instrument_schema['properties'][feature] and instrument_schema['properties'][feature]['data-type'] == 'ordinal':
				ordinal_features.add('%s:%s' % (instrument, feature))

with open('%s.json' % filename, 'r') as f:
    # Read in samples
    samples = json.load(f)

with open("%s.csv" % filename) as f:
	reader = csv.reader(f)
	header = next(reader)

	# pull labels for label file
	label_cols = ['identifier', 'clinical_diagnosis', 'gender', 'dataset', 'age', 'race', 'ethnicity', 
			'family', 'mother_id', 'father_id',
			'ADIR2003:diagnosis', 'ADIR2003:diagnosis_num_nulls',
			'ADOS_Module1:diagnosis', 'ADOS_Module1:diagnosis_num_nulls', 
			'ADOS_Module2:diagnosis', 'ADOS_Module2:diagnosis_num_nulls', 
			'ADOS_Module3:diagnosis', 'ADOS_Module3:diagnosis_num_nulls', 
			'ADOS_Module4:diagnosis', 'ADOS_Module4:diagnosis_num_nulls', 
			'SRS_Child:diagnosis', 'SRS_Child:diagnosis_num_nulls']
	label_cols = [x for x in label_cols if x in header]
	label_indices = [header.index(x) for x in label_cols]

	# Pull ordinal features that belong to the instruments we're interested in
	keep_cols = []
	for i, h in enumerate(header):
		if h in ordinal_features:
			keep_cols.append(i)
	print('Keeping %d features' % (len(keep_cols)))

	with open(filename + '_ordinal_labels.csv', 'w+') as label_outfile, open(filename + '_ordinal.csv', 'w+') as outfile:
		label_writer = csv.writer(label_outfile)
		writer = csv.writer(outfile)

		label_writer.writerow(label_cols + ['has_' + inst for inst in instruments])
		writer.writerow([header[i] for i in keep_cols])
		num_rows_written = 0
		for row, sample in zip(reader, samples):
			data = [("-1" if row[i] == '' or row[i] == 'None' else row[i]) for i in keep_cols]
			if len([d for d in data if d != 'None']) > 1:
				label_writer.writerow([("-1" if row[i] == '' or row[i] == 'None' else row[i]) for i in label_indices] + [1 if inst in sample else 0 for inst in instruments])
				writer.writerow(data)
				num_rows_written += 1
	print('Keeping %d rows' % num_rows_written)


