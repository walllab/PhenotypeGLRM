import numpy as np
import json
import csv
import random


# Read data
all_data = np.genfromtxt('../data/all_samples_filtered2.csv', delimiter=',', skip_header=True, missing_values=['None', ''])
m, n = all_data.shape

# Grab header
with open('../data/all_samples_filtered2.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)[1:]

# Grab labels
with open('../data/all_samples_filtered2_labels.csv', 'r') as f:
    reader = csv.reader(f)
    label_header = next(reader)
    labels = list(reader)

# Remove sample identifiers
sample_identifiers = all_data[:, 0]
all_data = all_data[:, 1:]

# Recode so that 0 means missing data
all_data[all_data == 0] = -1
all_data[np.isnan(all_data)] = 0

m, n = all_data.shape
train_data = all_data.astype(np.int64)
instrument_test_data = np.zeros(all_data.shape, dtype=np.int64)
entry_test_data = np.zeros(all_data.shape, dtype=np.int64)
print(train_data.shape)

# Recode each feature to skip missing categories
for i in range(n):
	options = [x for x in sorted(np.unique(all_data[:, i])) if x > 0]

	for j, option in enumerate(options):
		train_data[all_data[:, i]==option, i] = (j+1)

	print(sorted(np.unique(train_data[:, i])))

print('Responses', list(zip(*np.unique(train_data, return_counts=True))))

# ---------------------------- Mask whole instruments ----------------------------

instruments = ['ADIR', 'ADOS_Module1', 'ADOS_Module2', 'ADOS_Module3', 'ADOS_Module4', 'SRS']

# Pull instrument features and samples that have each instrument
features = []
samples = []
for instrument in instruments:
	features.append([i for i, x in enumerate(header) if x.startswith(instrument)])
	samples.append(set([i for i, x in enumerate(labels) if x[label_header.index('%s:diagnosis' % instrument)] != 'None']))
	print(instrument, 'features', len(features[-1]), 'samples', len(samples[-1]))

# Select non-overlapping sets of samples to mask such that each masked sample has more than one instrument
samples_with_multiple_instruments = set([i for i, x in enumerate(labels) if len([d for d in instruments if x[label_header.index('%s:diagnosis' % d)] != 'None'])>1])
print('samples with multiple instruments', len(samples_with_multiple_instruments))

masked = []
num_whole_instruments_masked = int(round(0.15*len(samples_with_multiple_instruments)/len(instruments)))
for i, instrument in enumerate(instruments):
	selectable = samples[i] & samples_with_multiple_instruments # samples must have more than one instrument
	selectable = selectable - set(sum(masked, [])) # remove samples that have already been masked
	masked.append(random.sample(selectable, num_whole_instruments_masked))
	print(instrument, 'masked', len(masked[-1]))

	instrument_test_data[np.ix_(masked[i], features[i])] = train_data[np.ix_(masked[i], features[i])]
	train_data[np.ix_(masked[i], features[i])] = 0

# ---------------------------- Mask entries ----------------------------
x, y = np.where(train_data != 0)
num_entries_masked = int(round(0.1*x.shape[0]))
entry_mask = random.sample(range(x.shape[0]), num_entries_masked)
entry_test_data[x[entry_mask], y[entry_mask]] = train_data[x[entry_mask], y[entry_mask]]
train_data[x[entry_mask], y[entry_mask]] = 0

print('Entries masked', len(entry_mask))
print('Train (should be all 0s)', train_data[x[entry_mask], y[entry_mask]])
print('Test (should have data)', entry_test_data[x[entry_mask], y[entry_mask]])

np.savetxt('../data/all_samples_filtered2_train.csv', train_data, delimiter=',', fmt='%d')
np.savetxt('../data/all_samples_filtered2_instrument_test.csv', instrument_test_data, delimiter=',', fmt='%d')
np.savetxt('../data/all_samples_filtered2_entry_test.csv', entry_test_data, delimiter=',', fmt='%d')


