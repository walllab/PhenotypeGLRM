import sys
import json
import csv

instrument = sys.argv[1]
qheader = 0 if len(sys.argv) <= 2 else int(sys.argv[2])

properties = {
	"age": {
		"description": "Age in months at interview",
		"type": ["integer", "null"],
		"minimum": 0
	},
	"interview_date": {
		"type": ["string", "null"]
	}
}

with open('../Phenotype/mssng/column.name.csv', 'r') as f:
	reader = csv.reader(f)
	for pieces in reader:
		if pieces[0] == instrument:
			if ':' not in pieces[3]:
				print(pieces[3])
			else:
				question, description = pieces[3].split(':', maxsplit=1)
				digit_index = qheader + ([c.isdigit() for c in question[qheader:]] + [False]).index(False)
				question = 'Q' + question[:qheader] + question[qheader:digit_index].zfill(2) + question[digit_index:]
				
				if question in properties:
					print('DUPLICATE', question, description)
				else:
					description = description.strip()
					options = [int(x[:x.find('=')]) for x in pieces[4].split()]
					ordinal_options = [x for x in options if x <= 6]
					coded_options = [x for x in options if x > 6]

					if len(ordinal_options) > 0:
						properties[question] = {
							"description": description,
							"enum": [None] + ordinal_options,
							"data-type": "ordinal"
						}
					elif 'Age' in description or 'month' in description or 'year' in description or 'Onset' in description:
						properties[question] = {
							'description': description,
							"type": ["integer", "null"],
							"maximum": 899,
							"not": {"enum": [991, 992, 996, 997, 998, 999]},
							"data-type": "interval"
						}
					else:
						print('NO OPTIONS', question, description)
					if len(coded_options) > 0:
						properties[question + 'a'] = {
							"description": 'Coded: ' + description,
							"enum": [None, 0] + coded_options,
							"data-type": "categorical"
						}
print(json.dumps(
	{
		'properties': properties, 
		'additionalProperties': False,
		'required': list(properties.keys())

	}, indent=4, sort_keys=True))
