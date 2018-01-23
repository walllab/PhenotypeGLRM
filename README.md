This is the code repository for the paper A Low Rank Model for Phenotype Imputation in Autism Spectrum Disorder presented at the AMIA 2018 Joint Summit. 

It has two modules:
1. A preprocessing module that aggregates phenotype data across a variety of formats using a jsonschema to validate the data.
2. An analysis module that uses the LowRankModels Julia package to train a specialized low-rank model for simultanesous imputation and clustering.
