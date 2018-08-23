import numpy as np
import json
import csv
import random
import sys

input_file = sys.argv[1] # ../data/all_samples_ordinal_cleaned.csv
sample_label_file = sys.argv[2] # ../data/all_samples_ordinal_labels.csv
feature_label_file = sys.argv[3] # ../data/all_samples_ordinal_cleaned_map.txt
output_stem = sys.argv[4] # ../data/all_samples_ordinal_test

# Read data
all_data = np.loadtxt(input_file, delimiter=',', dtype=int)
m, n = all_data.shape
print(m, n)

# Grab sample labels
with open(sample_label_file, 'r') as f:
    reader = csv.reader(f)
    label_header = next(reader)
    labels = list(reader)

# Grab feature labels
with open(feature_label_file, 'r') as f:
	header = [line.split('\t')[0] for line in f]

train_data = all_data.copy()

# ---------------------------- Mask whole instruments for Test ----------------------------
instruments = ['ADIR1995', 'ADIR2003',
	'ADOS2_Module_Toddler', 'ADOS_Module1', 'ADOS_Module2', 'ADOS_Module3', 'ADOS_Module4',
	'SRS_Adult', 'SRS_Child']

# Pull instrument features and samples that have each instrument
features = []
samples = []
for instrument in instruments:
	features.append([i for i, x in enumerate(header) if x.startswith(instrument)])
	samples.append(set([i for i, x in enumerate(labels) if x[label_header.index('has_%s' % instrument)] == '1']))
	print(instrument, 'features', len(features[-1]), 'samples', len(samples[-1]))

# Select non-overlapping sets of samples to mask such that each masked sample has more than one instrument
samples_with_multiple_instruments = set([i for i, x in enumerate(labels) if len([d for d in instruments if x[label_header.index('has_%s' % d)] == '1'])>1])
print('samples with multiple instruments', len(samples_with_multiple_instruments))

masked = []
for i, instrument in enumerate(instruments):
	selectable = samples[i] & samples_with_multiple_instruments # samples must have more than one instrument
	selectable = selectable - set(sum(masked, [])) # remove samples that have already been masked
	num_whole_instruments_masked = int(round(0.05*len(selectable)))
	masked.append(random.sample(selectable, num_whole_instruments_masked))
	print(instrument, 'masked', len(masked[-1]))

	instrument_test_data = np.zeros((m, n), dtype=int)
	instrument_test_data[np.ix_(masked[i], features[i])] = train_data[np.ix_(masked[i], features[i])]
	train_data[np.ix_(masked[i], features[i])] = 0

	np.savetxt(output_stem + '_instrument_%s.csv' % instrument, instrument_test_data.astype(int), delimiter=',', fmt='%d')

for ms, instrument in zip(masked, instruments):
	for i in ms:
		labels[i][label_header.index('has_%s' % instrument)] = '0'

with open(output_stem + '_labels.csv', 'w+') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(label_header)
    for l in labels:
    	writer.writerow(l)

# ---------------------------- Mask entries for Test ----------------------------
x, y = np.where(train_data != 0)
num_entries_masked = int(round(0.01*x.shape[0]))
entry_mask = random.sample(range(x.shape[0]), num_entries_masked)

entry_test_data = np.zeros((m, n), dtype=int)
entry_test_data[x[entry_mask], y[entry_mask]] = train_data[x[entry_mask], y[entry_mask]]
train_data[x[entry_mask], y[entry_mask]] = 0

print('Entries masked', len(entry_mask))
print('Train (should be all 0s)', train_data[x[entry_mask], y[entry_mask]])
print('Test (should have data)', entry_test_data[x[entry_mask], y[entry_mask]])

np.savetxt(output_stem + '_entry.csv', entry_test_data.astype(int), delimiter=',', fmt='%d')
np.savetxt(output_stem + '_train.csv', train_data.astype(int), delimiter=',', fmt='%d')

