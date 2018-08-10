import json

schema = {}
with open('adir_toddler.txt') as f:
	previous_q = None
	num_since = 2
	for line in f:
		if '.' in line[:10]:
			question, description = line.split('.', maxsplit=1)
			question = 'Q' + question.zfill(3)
			description = description.strip()
			previous_q, num_since = question, 2
		else:
			question = previous_q + '.' + str(num_since)
			num_since += 1
			description = line.strip()

		if 'AGE ' in description or 'Age ' in description or 'Onset ' in description or 'number' in description or 'length' in description:
			schema[question] = {
			"data-type": "interval",
			"description": description,
			"maximum": 899,
            "type": [ "integer", "null"]
            }
		else:
			schema[question] = {
			"data-type": "ordinal",
			"description": description,
			"enum": [None, 0, 1, 2, 3]
			}

			schema[question + 'a'] = {
			"data-type": "categorical",
			"description": "Coded: " + description,
			"enum": [None, 0, 8, 9]
			 }

print(json.dumps(
	{
		'properties': schema, 
		'additionalProperties': False,
		'required': list(schema.keys())

	}, indent=4, sort_keys=True))