using DataFrames
using LowRankModels

# To run this notebook, you need to have a data file available.
# You can either run the phenotype preprocessing scripts in ../preprocessing directory
# Or scp -r username@sherlock.stanford.edu:/scratch/PI/dpwall/DATA/phenotypes/jsonschema ../data

# Data
df = readtable("../data/all_samples_filtered_train.csv", header=false)
m, n = size(df)
println(m, n)

# Form sparse array
all_data = sparse(Array(df))
dropzeros!(all_data)
p = size(nonzeros(all_data), 1)

# Choose loss for each feature
losses = Array{Loss}(n)
for i=1:n
    options = unique(all_data[:, i])
    if length(options) == 3
        losses[i] = HingeLoss()
    else
        losses[i] = OrdinalHingeLoss(-1, maximum(options))
    end
end

for k=1:10
    rx = ZeroReg()
    ry = ZeroReg()

    glrm = GLRM(all_data, losses, rx, ry, k);
    params = SparseProxGradParams(max_iter=500)

    # cross validate
    train_error, test_error, train_glrms, test_glrms = cross_validate(glrm, nfolds=5, params=params)

    # write to file
    writecsv("../data/impute_cv_train_error$(k).csv", train_error)
    writecsv("../data/impute_cv_test_error$(k).csv", test_error)

    # fit full GLRM
    X,Y,ch = fit!(glrm, params, verbose=true); 

    # write to file
    writecsv("../data/impute_ordhinge_X$(k).csv", X)
    writecsv("../data/impute_ordhinge_Y$(k).csv", Y)
end

