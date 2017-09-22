import sys
import json
import csv
import functools
import jsonschema
import copy

##
# This function converts an item like 
# {
#   "node_item_1":"value_11",
#   "node_item_2":"value_12",
#   "node_item_3":"value_13",
#   "node_item_4_0":"sub_value_14", // Doesn't handle lists yet
#   "node_item_4_1":"sub_value_15", // Doesn't handle lists yet
#   "node_item_5_sub_item_1":"sub_item_value_11",
#   "node_item_5_sub_item_2_0":"sub_item_value_12",
#   "node_item_5_sub_item_2_0":"sub_item_value_13"
# }
# To
# {
#   "item_1":"value_11",
#   "item_2":"value_12",
#   "item_3":"value_13",
#   "item_4":["sub_value_14", "sub_value_15"], // Doesn't handle lists yet
#   "item_5":{
#       "sub_item_1":"sub_item_value_11",
#       "sub_item_2":["sub_item_value_12", "sub_item_value_13"]
#   }
# }
##

if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("\nUsage: python csv-to-json.py <csv_out_file_path> <json_in_file_path> <json_schema_path> <cols_to_remove>\n")
	else:
		#Reading arguments
		csv_file_path = sys.argv[1]
		json_file_path = sys.argv[2]
		json_schema_path = sys.argv[3]
		cols_to_remove = int(sys.argv[4])

		with open("AutismPhenotype.json") as schema_file:    
			pheno_schema = json.load(schema_file)

		index_to_keys = [tuple(['identifier'])] + [()]*cols_to_remove
		samples = []
		sample_example = {}
		with open(csv_file_path, 'r') as f:
			reader = csv.reader(f)

			# Create mapping between indices and entries
			header = next(reader)
			for h in header[(cols_to_remove+1):]:
				keys = [x[:-2] if x.endswith('_1') else x for x in h.split(':')]
				index_to_keys.append(tuple(keys))
				entry_place = sample_example
				for key in keys[:-1]:
					entry_place[key] = {}
					entry_place = entry_place[key]


			# Now use mapping to fill in json schema
			for row in reader:
				sample = copy.deepcopy(sample_example)
				for i, v in enumerate(row):
					entry_place = sample
					keys = index_to_keys[i]
					if len(keys) > 0:
						for key in keys[:-1]:
							entry_place = entry_place[key]
						try:
							value = int(v)
						except:
							value = v
						entry_place[keys[-1]] = value

				# Fill in missing entries for present instruments
				for key in sample:
					if isinstance(sample[key], dict):
						for feature in pheno_schema['definitions'][key]['properties']:
							if feature not in sample[key]:
								sample[key][feature] = None

				jsonschema.validate(sample, pheno_schema)
				samples.append(sample)

		# Write json to file
		with open(json_file_path, 'w+') as outfile:
			json.dump(samples, outfile, sort_keys=True, indent=4)

		print("Just completed writing json file with %d samples" % len(samples))
