import numpy as np
import json
import csv
import random


# Read data
all_data = np.genfromtxt('../data/all_samples_ordinal.csv', delimiter=',', skip_header=True, missing_values=['None', ''], dtype=int)
m, n = all_data.shape

# Grab header
with open('../data/all_samples_ordinal.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)[1:]

# Grab labels
with open('../data/all_samples_ordinal_labels.csv', 'r') as f:
    reader = csv.reader(f)
    label_header = next(reader)
    labels = list(reader)

# pull individuals with autism and known sex
diag_index = label_header.index('diagnosis')
sex_index = label_header.index('gender')

filtered_indices = []
for i, sample_labels in enumerate(labels):
	if sample_labels[diag_index] == 'Autism' and sample_labels[sex_index] != 'None':
		filtered_indices.append(i)
all_data = all_data[filtered_indices, :]
labels = [labels[i] for i in filtered_indices]

# Remove sample_identifiers
sample_identifiers = all_data[:, 0]
all_data = all_data[:, 1:]

# Recode so that 0 means missing data 1, 2, 3, etc mean responses
all_data += 1
all_data[np.isnan(all_data)] = 0

# pull certain instruments
item_indices = []
for i, h in enumerate(header):
	if h.startswith('ADIR') or h.startswith('ADOS_Module') or h.startswith('SRS_Adult') or h.startswith('SRS_Child'):
		item_indices.append(i)
all_data = all_data[:, item_indices]

# Add sex columns
print(len(labels), all_data.shape)
all_data = np.insert(all_data, 0, [1 if x[sex_index] == 'Male' else 0 for x in labels], axis=1)
all_data = np.insert(all_data, 0, [1 if x[sex_index] == 'Female' else 0 for x in labels], axis=1)
labels = ['Male', 'Female'] + labels

# Recode each feature to skip missing categories
m, n = all_data.shape
for i in range(n):
	options = [x for x in sorted(np.unique(all_data[:, i])) if x > 0]

	for j, option in enumerate(options):
		all_data[all_data[:, i]==option, i] = (j+1)

print(m, n)
print('Responses', list(zip(*np.unique(all_data.astype(int), return_counts=True))))

train_data = all_data.copy()

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
for i, instrument in enumerate(instruments):
	selectable = samples[i] & samples_with_multiple_instruments # samples must have more than one instrument
	selectable = selectable - set(sum(masked, [])) # remove samples that have already been masked
	num_whole_instruments_masked = int(round(0.05*len(selectable)))
	masked.append(random.sample(selectable, num_whole_instruments_masked))
	print(instrument, 'masked', len(masked[-1]))

	instrument_test_data = np.zeros((m, n), dtype=int)
	instrument_test_data[np.ix_(masked[i], features[i])] = train_data[np.ix_(masked[i], features[i])]
	train_data[np.ix_(masked[i], features[i])] = 0

	np.savetxt('../data/all_samples_ordinal_test_instrument_%s.csv', instrument_test_data.astype(int), delimiter=',', fmt='%d')

# ---------------------------- Mask entries ----------------------------
x, y = np.where(train_data != 0)
num_entries_masked = int(round(0.1*x.shape[0]))
entry_mask = random.sample(range(x.shape[0]), num_entries_masked)

print('Entries masked', len(entry_mask))
print('Train (should be all 0s)', train_data[x[entry_mask], y[entry_mask]])
print('Test (should have data)', entry_test_data[x[entry_mask], y[entry_mask]])

entry_test_data = np.zeros((m, n), dtype=int)
entry_test_data[x[entry_mask], y[entry_mask]] = train_data[x[entry_mask], y[entry_mask]]
train_data[x[entry_mask], y[entry_mask]] = 0

np.savetxt('../data/all_samples_ordinal_test_entry.csv', entry_test_data.astype(int), delimiter=',', fmt='%d')
np.savetxt('../data/all_samples_ordinal_train.csv', train_data.astype(int), delimiter=',', fmt='%d')
