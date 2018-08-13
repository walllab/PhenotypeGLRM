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

# Pull ordinal features
with open(filename + '.csv', 'r') as infile, open(filename + '_labels.csv', 'r') as labelfile:
	reader = csv.reader(infile)
	header = next(reader)

	label_reader = csv.reader(labelfile)
	label_header = next(label_reader)

	diag_index = label_header.index('diagnosis')
	sex_index = label_header.index('gender')

	filtered_data = []
	filtered_labels = []
	for sample_labels in label_reader:
		sample= next(reader)

		#if sample_labels[diag_index] == 'Autism' and sample_labels[sex_index] != 'None':
		if sample_labels[sex_index] != 'None':
			filtered_data.append(sample)
			filtered_labels.append(sample_labels)

print('Keeping %d samples' % (len(filtered_data)))

with open(filename + '_diagsex_labels.csv', 'w+') as label_outfile, open(filename + '_diagsex.csv', 'w+') as outfile:
	label_writer = csv.writer(label_outfile)
	writer = csv.writer(outfile)

	label_writer.writerow(label_header)
	writer.writerow(header)
	for labels, sample in zip(filtered_labels, filtered_data):
		label_writer.writerow(labels)
		writer.writerow(sample)


