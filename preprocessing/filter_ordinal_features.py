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

with open("AutismPhenotype.json") as schema_file:    
	pheno_schema = json.load(schema_file)

# Accumulate missing data counts for rows and columns
with open(filename + '.csv', 'r') as infile:
	reader = csv.reader(infile)
	col_null_counts = [0.0]*len(next(reader))
	row_null_counts = []

	for row in reader:
		c = 0
		for j, e in enumerate(row):
			if e == '' or e == 'None':
				col_null_counts[j] += 1
				c += 1
		row_null_counts.append(c)

col_null_counts = [x/len(row_null_counts) for x in col_null_counts]
row_null_counts = [x/len(col_null_counts) for x in row_null_counts]

# Pull ordinal features
with open(filename + '.csv', 'r') as infile:
	reader = csv.reader(infile)
	header = next(reader)

	label_cols = [
		header.index('identifier'), 
		header.index('diagnosis'), header.index('ADIR:diagnosis'), header.index('ADIR:diagnosis_num_nulls'), header.index('ADIR:communication'), header.index('ADIR:social_interaction'), header.index('ADIR:restricted_repetitive_behavior'),
		header.index('ADOS:diagnosis'), header.index('ADOS:diagnosis_num_nulls'), header.index('ADOS:communication'), header.index('ADOS:social_interaction'), header.index('ADOS:restricted_repetitive_behavior'),
		header.index('SRS:diagnosis'), header.index('SRS:diagnosis_num_nulls'), header.index('SRS:social_awareness'), header.index('SRS:social_cognition'), header.index('SRS:social_communication'), header.index('SRS:social_motivation'), header.index('SRS:autistic_mannerisms'),
		header.index('cpea_diagnosis'), header.index('cpea_adjusted_diagnosis')
	]

	keep_cols = [header.index('identifier')]

	# Pull ordinal features
	for i, h in enumerate(header):
		if col_null_counts[i] <= 1: #.4:
			if ':' in h:
				pieces = h.strip().split(':')
				json_item = pheno_schema['definitions']
				for piece in pieces:
					if piece in json_item:
						json_item = json_item[piece]
					elif piece in json_item['properties']:
						json_item = json_item['properties'][piece]
					else:
						print('Problem!', piece)
				if 'data-type' in json_item and json_item['data-type'] == 'ordinal' and not pieces[0].startswith('ADOS_'):
					keep_cols.append(i)

	print('Keeping %d features' % (len(keep_cols)-1))

	with open(filename + '_filtered_labels.csv', 'w+') as label_outfile:
		with open(filename + '_filtered.csv', 'w+') as outfile:
			label_writer = csv.writer(label_outfile)
			writer = csv.writer(outfile)

			label_writer.writerow([header[i] for i in label_cols])
			writer.writerow([header[i] for i in keep_cols])
			for i, row in enumerate(reader):
				if row_null_counts[i] <= 1: #.6:
					label_writer.writerow([("None" if row[i] == '' else row[i]) for i in label_cols])
					writer.writerow([("None" if row[i] == '' else row[i]) for i in keep_cols])


