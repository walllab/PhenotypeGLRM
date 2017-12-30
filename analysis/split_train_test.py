import numpy as np
import json
import csv
import random


# Read data
all_data = np.genfromtxt('../data/all_samples_filtered.csv', delimiter=',', skip_header=True, missing_values=['None', ''])
m, n = all_data.shape

# Grab header
with open('../data/all_samples_filtered.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)[1:]

# Grab labels
with open('../data/all_samples_filtered_labels.csv', 'r') as f:
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
# Pull instrument features
adir_features = [i for i, x in enumerate(header) if x.startswith('ADIR')]
ados_features = [i for i, x in enumerate(header) if x.startswith('ADOS')]
srs_features = [i for i, x in enumerate(header) if x.startswith('SRS')]
print('ADIR features', len(adir_features), 'ADOS features', len(ados_features), 'SRS features', len(srs_features))

# Pull samples with each instrument
adir_samples = set([i for i, x in enumerate(labels) if x[label_header.index('ADIR:diagnosis')] != 'None'])
ados_samples = set([i for i, x in enumerate(labels) if x[label_header.index('ADOS:diagnosis')] != 'None'])
srs_samples = set([i for i, x in enumerate(labels) if x[label_header.index('SRS:diagnosis')] != 'None'])
print('ADIR samples', len(adir_samples), 'ADOS samples', len(ados_samples), 'SRS samples', len(srs_samples))

# Select non-overlapping sets of samples to mask such that each masked sample has more than one instrument
selectable = adir_samples & ados_samples & srs_samples
num_whole_instruments_masked = int(round(0.15*len(selectable)*0.33))

adir_mask = random.sample(selectable, num_whole_instruments_masked)
ados_mask = random.sample(selectable - set(adir_mask), num_whole_instruments_masked)
srs_mask = random.sample(selectable - set(adir_mask) - set(ados_mask), num_whole_instruments_masked)

print('Samples masked', len(adir_mask), len(ados_mask), len(srs_mask), len(set(adir_mask) & set(ados_mask)), len(set(ados_mask) & set(srs_mask)), len(set(adir_mask) & set(srs_mask)))

instrument_test_data[np.ix_(adir_mask, adir_features)] = train_data[np.ix_(adir_mask, adir_features)]
train_data[np.ix_(adir_mask, adir_features)] = 0
instrument_test_data[np.ix_(ados_mask, ados_features)] = train_data[np.ix_(ados_mask, ados_features)]
train_data[np.ix_(ados_mask, ados_features)] = 0
instrument_test_data[np.ix_(srs_mask, srs_features)] = train_data[np.ix_(srs_mask, srs_features)]
train_data[np.ix_(srs_mask, srs_features)] = 0

print('Train (should be all 0s)', train_data[np.ix_(adir_mask, adir_features)])
print('Test (should have data)', instrument_test_data[np.ix_(adir_mask, adir_features)])

# ---------------------------- Mask entries ----------------------------
x, y = np.where(train_data != 0)
num_entries_masked = int(round(0.1*x.shape[0]))
entry_mask = random.sample(range(x.shape[0]), num_entries_masked)
entry_test_data[x[entry_mask], y[entry_mask]] = train_data[x[entry_mask], y[entry_mask]]
train_data[x[entry_mask], y[entry_mask]] = 0

print('Entries masked', len(entry_mask))
print('Train (should be all 0s)', train_data[x[entry_mask], y[entry_mask]])
print('Test (should have data)', entry_test_data[x[entry_mask], y[entry_mask]])

np.savetxt('../data/all_samples_filtered_train.csv', train_data, delimiter=',', fmt='%d')
np.savetxt('../data/all_samples_filtered_instrument_test.csv', instrument_test_data, delimiter=',', fmt='%d')
np.savetxt('../data/all_samples_filtered_entry_test.csv', entry_test_data, delimiter=',', fmt='%d')


