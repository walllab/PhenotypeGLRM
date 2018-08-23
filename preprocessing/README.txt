This python package can aggregate and correct data from our four phenotype datasets:
	Autism Genetic Resource Exchange (AGRE)
	Autism Consortium (AC)
	National Database for Autism Research (NDAR)
	Simons Simplex Collection (SSC)

for the following instruments:
	Autism Diagnostic Interview-Revised (ADIR)
	Autism Diagnostic Observation Schedule 2 (ADOS)*

* As a note, ADOS contains four modules, each of which are administered to individuals in different age brackets. We aggregate these modules by item.

The data from these datasets exists in csv and txt files on sherlock at /scratch/PI/dpwall/DATA/phenotypes. Each dataset uses a different file structure (sometimes multiple structures) to store the data. I used a jsonschema (which can be found in AutismPhenotype.json) to aggregate the data and to be sure that is conforms to the instruments themselves.

This package is structured as a multi-stage pipeline.

1. aggregate_phenotype.py - Pulls data from raw files, aggregates it into json, then validates this json with the jsonschema
2. remove_empty.py - Removes subjects that do not have data for any instrument. This occurs because some of our datasets include all study participants, even if they do not have phenotypic data. 
3. aggregate_ados.py - Aggregates ADOS data across all four modules, item by item, to create an ADOS dataset that is comparable across individuals
4. assign_diagnosis.py - Assigns diagnoses to each instrument based on item-level data for each instrument. This script uses the diagnostic instructions provided with each instrument.
5. json-to-csv.py - Transforms json into csv form for ease of analysis.
6. filter_ordinal_features.py - Pulls columns of interet for analysis. Discards age of onset questions, special codes, and individual ADOS modules (in favor of the aggregated ADOS data).

Here's an example run:
python3 aggregate_phenotype.py ../Phenotype
python3 remove_empty.py ../data/all_samples_stage1.json ../data/all_samples_stage2.json
python3 assign_diagnosis.py ../data/all_samples_stage2.json ../data/all_samples.json
python3 json-to-csv.py ../data/all_samples.json ../data/all_samples.csv
python3 filter_ordinal_features.py ../data/all_samples
python3 clean_ordinals.py ../data/all_samples_ordinal.csv ../data/all_samples_ordinal_cleaned.csv
#python3 filter_autism_known_sex.py ../data/all_samples_ordinal

# Splitting training/testing
python split_train_test.py ../data/all_samples_ordinal_cleaned.csv ../data/all_samples_ordinal_labels.csv ../data/all_samples_ordinal_cleaned_map.txt ../data/all_samples_ordinal_test
python split_train_test.py ../data/all_samples_ordinal_test_train.csv ../data/all_samples_ordinal_test_labels.csv ../data/all_samples_ordinal_cleaned_map.txt ../data/all_samples_ordinal_cv0
