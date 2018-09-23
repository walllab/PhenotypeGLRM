import numpy as np

datasets = ['train', 'ADIR1995', 'ADIR2003', 
'ADOS_Module1', 'ADOS_Module2', 'ADOS_Module3', 'ADOS_Module4', 'ADOS2_Module_Toddler',
'SRS_Adult', 'SRS_Child', 'entry']

# load data
actual_data = [[None]*5 for _ in datasets]
for fold in range(0, 5):
	for i, d in enumerate(datasets):
		actual_data[i][fold] = np.loadtxt('all_samples_ordinal_cv%d_%s.csv' % (fold, instrument), delimiter=',', dtype=int)

# load imputed data
imputed_data = [None]*5
for i, k in enumerate([5, 10, 15, 20, 25]):
	imputed_data[i] = np.loadtxt('all_samples_ordinal_cv%d_%s.csv' % (fold, instrument), delimiter=',', dtype=int)