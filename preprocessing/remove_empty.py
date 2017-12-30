import json
import sys
from collections import defaultdict

with open(sys.argv[1], 'r') as infile:
	# Read in samples
	samples = json.load(infile)
print('Starting with %d samples' % len(samples))

# Find empty instruments
to_be_removed = defaultdict(list)
for i, sample in enumerate(samples):
	for key, value in sample.items():
		if isinstance(value, dict):
			# this is an instrument
			nonnull_items = len([v for k, v in value.items() if v is not None and k.startswith('Q')])
			if nonnull_items == 0:
				to_be_removed[key].append(i)

# Remove empty instruments
for instrument, indices in to_be_removed.items():
	for index in indices:
		del samples[index][instrument]
	print('Removed %d %s instruments' % (len(indices), instrument))

# Find individuals with no instruments
to_be_removed = []
for i, sample in enumerate(samples):
	num_instruments = len([k for k, v in sample.items() if isinstance(v, dict) and k != 'Medical History'])
	if num_instruments == 0:
		to_be_removed.append(i)

# Remove samples
for index in reversed(to_be_removed):
	del samples[index]
print('Removed %d samples' % len(to_be_removed))

# Write json to file
with open(sys.argv[2], 'w+') as outfile:
	print(len(samples))
	json.dump(samples, outfile, sort_keys=True, indent=4)