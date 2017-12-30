import json
import sys

# Read in samples
with open(sys.argv[1], 'r') as infile:
	samples = json.load(infile)

	
# Write to file
with open(sys.argv[2], 'w+') as outfile:
	json.dump([x for x in samples if 'ADIR' in x and 'ADOS' in x], outfile, sort_keys=True, indent=4)