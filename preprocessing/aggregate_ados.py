import json
import jsonschema
import sys
from os import path

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from preprocessing import create_new_instrument

# This script aggregates the four ADOS modules item by item into an "ADOS" instrument. I only combine items
# if they have identical or very similar descriptions. I also retain all items, even if they don't
# merge across modules. This means we don't lose very much information between any given module and the
# aggregated ADOS instrument.

# This code requires aggregate_phenotype.py to already have been run.
# It outputs a file called all_samples_stage2.json which contains a new ADOS instrument for all
# samples with any of the four ADOS modules.
# It is meant to be run as part of a multi-stage pipeline described in the README.

# The code can be run with:
# python3 aggregate_ados.py

with open("../data/all_samples_stage1.json") as f:    
	samples = json.load(f)

with open("AutismPhenotype.json") as schema_file:    
	pheno_schema = json.load(schema_file)

feature_mapping = {
	'ADOS_Module1': {
		"QA01": "QA01", "QA02": "QA11", "QA03": "QA02", "QA04": "QA03", "QA05": "QA04", 
		"QA06": "QA12", "QA07": "QA07", "QA08": "QA10",
		"QB01": "QB01", "QB02": "QB17", "QB03": "QB02", "QB04": "QB16", "QB05": "QB04",
		"QB06": "QB07", "QB07": "QB19", "QB08": "QB21", "QB09": "QB08", "QB10": "QB10", 
		"QB11": "QB09", "QB12": "QB13", "QB13.1": "QB11", "QB13.2": "QB23", "QB14": "QB14", "QB15": "QB22",
		"QB16": "QB15",
		"QC01": "QC01", "QC02": "QC02",
		"QD01": "QD01", "QD02": "QD02", "QD03": "QD03", "QD04": "QD04",
		"QE01": "QE01", "QE02": "QE02", "QE03": "QE03"
	},
	'ADOS_Module2': {
		"QA01": "QA01", "QA02": "QA02", "QA03": "QA03", "QA04": "QA04", "QA05": "QA09",
		"QA06": "QA07", "QA07": "QA10",
		"QB01": "QB01", "QB02": "QB02", "QB03": "QB04", "QB04": "QB07", "QB05": "QB08",
		"QB06": "QB10", "QB07": "QB09", "QB08": "QB13", "QB09.1": "QB11", "QB09.2": "QB23", "QB10": "QB14",
		"QB11": "QB12", "QB12": "QB15", 
		"QC01": "QC01", "QC02": "QC02",
		"QD01": "QD01", "QD02": "QD02", "QD03": "QD03", "QD04": "QD04",
		"QE01": "QE01", "QE02": "QE02", "QE03": "QE03"
	},
	'ADOS_Module3': {
		"QA01": "QA01", "QA02": "QA02", "QA03": "QA03", "QA04": "QA04", "QA05": "QA05", 
		"QA06": "QA06", "QA07": "QA08", "QA08": "QA09", "QA09": "QA10",
		"QB01": "QB01", "QB02": "QB02", "QB03": "QB03", "QB04": "QB04", "QB05": "QB05",
		"QB06": "QB06", "QB07": "QB13", "QB08": "QB11", "QB09": "QB14", "QB10": "QB12",
		"QB11": "QB15",
		"QC01": "QC02",
		"QD01": "QD01", "QD02": "QD02", "QD03": "QD03", "QD04": "QD04", "QD05": "QD05",
		"QE01": "QE01", "QE02": "QE02", "QE03": "QE03"

	},
	'ADOS_Module4': {
		"QA01": "QA01", "QA02": "QA02", "QA03": "QA03", "QA04": "QA04", "QA05": "QA05", 
		"QA06": "QA06", "QA07": "QA08", "QA08": "QA09", "QA09": "QA10", "QA10": "QA13",
		"QB01": "QB01", "QB02": "QB02", "QB03": "QB03", "QB04": "QB04", "QB05": "QB18",
		"QB06": "QB05", "QB07": "QB06", "QB08": "QB20", "QB09": "QB13", "QB10": "QB11",
		"QB11": "QB14", "QB12": "QB12", "QB13": "QB15",
		"QC01": "QC02",
		"QD01": "QD01", "QD02": "QD02", "QD03": "QD03", "QD04": "QD04", "QD05": "QD05",
		"QE01": "QE01", "QE02": "QE02", "QE03": "QE03"
	}
}

ados_instruments = ['ADOS_Module1', 'ADOS_Module2', 'ADOS_Module3', 'ADOS_Module4']


if __name__ == '__main__':
	for sample in samples:
		ados_found = False
		for instrument in ados_instruments:
			if not ados_found and instrument in sample:
				ados_found = True

				# Construct an ados instrument
				sample['ADOS'] = create_new_instrument('ADOS', pheno_schema)
				sample['ADOS']['module'] = instrument

				#Map values
				for key, value in sample[instrument].items():
					if key in feature_mapping[instrument]:
						sample['ADOS'][feature_mapping[instrument][key]] = value
					elif key in sample['ADOS']:
						sample['ADOS'][key] = value

		jsonschema.validate(sample, pheno_schema)

	# Write json to file
	with open('../data/all_samples_stage2.json', 'w+') as outfile:
		print(len(samples))
		json.dump(samples, outfile, sort_keys=True, indent=4)
