import json
import jsonschema

with open('schemas/Individual.json') as schema_file:    
	pheno_schema = json.load(schema_file)
print(pheno_schema)

jsonschema.validate({
	'identifier': 'x',
	'ADIR': {}
	}, pheno_schema)