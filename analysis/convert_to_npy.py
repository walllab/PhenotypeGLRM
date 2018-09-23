import numpy as np

datasets = ['train', 'instrument_ADIR1995', 'instrument_ADIR2003', 
'instrument_ADOS_Module1', 'instrument_ADOS_Module2', 'instrument_ADOS_Module3', 'instrument_ADOS_Module4', 'instrument_ADOS2_Module_Toddler',
'instrument_SRS_Adult', 'instrument_SRS_Child', 
            'entry']

for fold in range(0, 10):
    for d in datasets:
        filename = '../data/all_samples_ordinal_cv%d_%s' % (fold, d)
        print(filename)
        A = np.loadtxt(filename + '.csv', delimiter=',', dtype=int)
        np.save(filename, A)