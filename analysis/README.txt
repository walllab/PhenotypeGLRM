This directory contains jupyter notebooks and scripts used to train models and analyze data.

1. split_train_test.py - A python script that splits our dataset into training and testing data. Test data is composed of subjects with masked entries as well as entire masked instruments. The training/testing split is used to evaluate imputation performance.
2. bvs_entry_param_tuning.jl - Runs cross validation on a generalized low rank model with a multidimensional ordinal loss, simplex constraint on the X factor and L2 regularization on the Y factor. This is used to select the dimension of the low rank space, k for entry-level imputation.
3. bvs_wholeinst_param_tuning.jl - Runs cross validation on a generalized low rank model with a multidimensional ordinal loss, simplex constraint on the X factor and L2 regularization on the Y factor. This is used to select the dimension of the low rank space, k for instrument-level imputation.
4. bvs_full_model.jl - Trains our model on the full dataset - used only for cluster analysis.
5. Dataset-Overview.ipynb - A python notebook generating plots showing basic information about our dataset of phentoypes.
6. Baseline-Models.ipynb - A python notebook that fits several baseline imputation models including median-impute, knn-impute, and MICE (uses fancyimpute package).
7. Evaluate-Imputation.ipynb - A python notebook that generates imputation performance measurements and plots.
8. Evaluate-Clusters.ipynb - A python notebook that explores the low-rank clusters and generates plots.
9. Evaluate-Multidimensional-Loss.ipynb - A python notebook that explores the performance of the multidimensional ordinal loss.