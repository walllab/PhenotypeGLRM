
def create_new_instrument(instrument, schema):
	return dict([(key, None) for key in schema['definitions'][instrument]['properties'].keys()])