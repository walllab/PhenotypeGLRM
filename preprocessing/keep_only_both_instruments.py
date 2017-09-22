import json

# Read in samples
with open('../data/all_samples.json', 'r') as infile:
	samples = json.load(infile)

	
# Write to file
with open('../data/all_samples_both_instruments.json', 'w+') as outfile:
	json.dump([x for x in samples if 'ADIR' in x and 'ADOS' in x], outfile, sort_keys=True, indent=4)