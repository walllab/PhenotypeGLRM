import json
import jsonschema

# This script "imputes" ADIR values of the form Q**.1 Q**.2. These questions ask for behaviors that are CURRENTLY occuring (Q**.1)
# and behaviors that have EVER occured (Q**.2). Many samples have only a single value for these questions (generally Q**.1) which
# causes trouble at the diagnosis stage because diagnosis is done with Q**.2 questions. Therefore, if the individual has a score
# for one question but not the other, we fill in the other with the same score.

# The code can be run with:
# python3 aggregate_ados.py

with open("../data/all_samples_stage2.json") as f:    
	samples = json.load(f)

with open("AutismPhenotype.json") as schema_file:    
	pheno_schema = json.load(schema_file)

replaced_current = 0
replaced_ever = 0
for sample in samples:
	if 'ADIR' in sample:
		for feature in pheno_schema['definitions']['ADIR']['properties'].keys():
			if feature.startswith('Q') and (feature.endswith('.1')):
				current_key = feature
				ever_key = feature[:-2] + '.2'
				current_answer = sample['ADIR'][current_key]
				ever_answer = sample['ADIR'][ever_key]

				if current_answer is not None and ever_answer is not None:
					pass
				elif current_answer is None and ever_answer is not None:
					sample['ADIR'][current_key] = ever_answer
					replaced_current += 1
				elif current_answer is not None and ever_answer is None:
					sample['ADIR'][ever_key] = current_answer
					replaced_ever += 1
				elif current_answer is None and ever_answer is None:
					pass

print('Replaced current:', replaced_current, 'Replaced ever:', replaced_ever)


# Write json to file
with open('../data/all_samples_stage3.json', 'w+') as outfile:
	print(len(samples))
	json.dump(samples, outfile, sort_keys=True, indent=4)
