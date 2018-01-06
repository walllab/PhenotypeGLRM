using DataFrames
using LowRankModels


# Pull command line arguments
data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
nfolds = parse(Int64, ARGS[3])
@show data_directory, k, nfolds

# Read in training data
df = readtable(string(data_directory, "/all_samples_filtered_train.csv"), header=false)
m, n = size(df)

# Form sparse array
all_data = sparse(Array(df))
dropzeros!(all_data)
p = size(nonzeros(all_data), 1)

# Offset values so that 0 indicates missing and all other entries are 1, 2, 3, etc
all_data[all_data .> 0] = all_data[all_data .> 0] + 1
all_data[all_data.==-1] = 1

# Pull observed (nonzero) entries
i, j, v = findnz(all_data)
obs = collect(zip(i, j))

@show maximum(all_data), minimum(all_data), size(obs, 1)

# construct the model
rx, ry = NonNegOneReg(1.0), QuadReg(.01)

losses = Array{Loss}(n)
D = 0
for i=1:n
    options = unique(all_data[:, i])
    num_options = max(maximum(options), 3) # Min 3 levels to keep loss well-defined
    losses[i] = BvSLoss(num_options)
    D += (num_options-1)
end
@show m, n, D


# Initialize X and Y
Xinit = randn(k, m)
Yord = randn(k, D)
yidxs = get_yidxs(losses)
for j=1:n
    prox!(ry, view(Yord,:,yidxs[j]), 1)
end

glrm = GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=false, X=Xinit, Y=Yord);

# cross validate
train_error, test_error, train_glrms, test_glrms = cross_validate(glrm, nfolds=nfolds, use_folds=1, params=ProxGradParams(max_iter=500), verbose=true)

# write to file
#writecsv(string(data_directory, "/impute_bvs_simplex_cv_train_error$(k)_$(10.0^(reg-2)).csv"), train_error)
#writecsv(string(data_directory, "/impute_bvs_simplex_cv_test_error$(k)_$(10.0^(reg-2)).csv"), test_error)

# fit full model
@time X,Y,ch = fit!(glrm, ProxGradParams(max_iter=500));

# write to file
writecsv(string(data_directory, "/impute_bvs_simplex_initk_X$(k).csv"), X)
writecsv(string(data_directory, "/impute_bvs_simplex_initk_Y$(k).csv"), Y)
writecsv(string(data_directory, "/impute_bvs_simplex_initk_Z$(k).csv"), impute(glrm))

