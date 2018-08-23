import numpy as np
import sys
from collections import Counter

input_file = sys.argv[1] # ../data/all_samples_ordinal.csv
output_file = sys.argv[2] # ../data/all_samples_ordinal_cleaned.csv

# Our goal here is to remove features that are mostly missing and 
# ordinal values that rarely occur - this will improve computational efficiency when fitting the model
# we also identify boolean variables and map them to {-1, 1}
# we transform values so that 0 indicates missing
# we remove sample identifiers

# Read data
all_data = np.loadtxt(input_file, delimiter=',', skiprows=1, dtype=int)
m, n = all_data.shape
print(m, n)

# Grab header
with open(input_file, 'r') as f:
    header = next(f).split(',')

# Recode so that 0 means missing data 1, 2, 3, etc mean responses
all_data += 1

# Recode each feature to skip missing categories
m, n = all_data.shape
option_map = [] # for each feature, give an ordered list of options
for i in range(n):
	options, count = np.unique(all_data[:, i], return_counts=True)
	option_to_count = dict(zip(options, count))
	options = [x for x in sorted(options) if x > 0 and option_to_count[x]>100]
	option_map.append(options)

# remove features with only one option
header = [h for h, os in zip(header, option_map) if len(os)>1]
all_data = all_data[:, [i for i, os in enumerate(option_map) if len(os)>1]]
option_map = [os for os in option_map if len(os)>1]
print('Num options', Counter([len(x) for x in option_map]))

new_all_data = np.zeros((m, len(option_map)), dtype=int)
with open(output_file[:-4] + '_map.txt', 'w+') as outf:
	for i, options in enumerate(option_map):
		if len(options) == 2:
			new_all_data[all_data[:, i]==options[0], i] = -1
			new_all_data[all_data[:, i]==options[1], i] = 1
		else:
			for j, option in enumerate(options):
				new_all_data[all_data[:, i]==option, i] = (j+1)
		outf.write('%s\t%d\t%s\n' % (header[i], len(options), str([x-1 for x in options])))
all_data = new_all_data

# remove mostly missing features
percent_missing = np.sum(all_data==0, axis=0)/all_data.shape[0]
header = [h for h, m in zip(header, percent_missing) if m < 1]
all_data = all_data[:, percent_missing < 1]
print('Mostly missing features removed, left with %d' % all_data.shape[1])

print(m, n)
print('Responses', list(zip(*np.unique(new_all_data, return_counts=True))))
np.savetxt(output_file, new_all_data, delimiter=',', fmt='%d')

