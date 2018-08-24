import numpy as np
import sys
from collections import Counter

input_file = sys.argv[1] # ../data/all_samples_ordinal_cleaned.csv
input_label_file = sys.argv[2] # ../data/all_samples_ordinal_labels.csv
output_file = sys.argv[3] # ../data/all_samples_ordinal_cleaned_gender

# Our goal here is to pull only individuals with known sex
# and to reorder so that individuals with unknown diagnosis are at the bottom

# Read data
all_data = np.loadtxt(input_file, delimiter=',', skiprows=0, dtype=int)
m, n = all_data.shape
print(m, n)

# Grab label info
gender_diag = np.zeros((m, 2), dtype=int)
label_lines = []
with open(input_label_file, 'r') as f, open(output_file + '_labels.csv', 'w+') as outf:
	line = next(f)
	header = line.split(',')
	gender_index = header.index('gender')
	diag_index = header.index('clinical_diagnosis')

	outf.write(line)
	for i, line in enumerate(f):
		pieces = line.split(',')
		if pieces[gender_index] == 'Male':
			gender_diag[i, 0] = 1
		elif pieces[gender_index] == 'Female':
			gender_diag[i, 0] = -1

		if pieces[diag_index] in ['Autism', 'PDD-NOS', 'Asperger']:
			gender_diag[i, 1] = 1
		elif pieces[diag_index] == 'Control':
			gender_diag[i, 1] = -1

		label_lines.append(line)

	pull_indices = np.concatenate((np.where((gender_diag[:, 0] != 0) & (gender_diag[:, 1] != 0))[0], np.where((gender_diag[:, 0] != 0) & (gender_diag[:, 1] == 0))[0]))
	for i in pull_indices:
		outf.write(label_lines[i])

np.savetxt(output_file + '.csv', all_data[pull_indices, :], delimiter=',', fmt='%d')
np.savetxt(output_file + '_gendiag.csv', gender_diag[pull_indices, :], delimiter=',', fmt='%d')
