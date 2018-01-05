using DataFrames
using LowRankModels

data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
nfolds = parse(Int64, ARGS[3])

@show data_directory, k, nfolds

# Data
df = readtable(string(data_directory, "/all_samples_filtered_train.csv"), header=false, nastrings=["0"])
obs = observations(df)
[df[isna.(df[nm]), nm] = 0 for nm in names(df)]
m, n = size(df)

# Form sparse array
all_data = sparse(Array(df))
dropzeros!(all_data)
p = size(nonzeros(all_data), 1)

all_data_offset = copy(all_data)
all_data_offset[all_data .> 0] = all_data[all_data .> 0] + 1
all_data_offset[all_data.==-1] = 1
@show maximum(all_data_offset), minimum(all_data_offset), size(nonzeros(all_data_offset), 1)

losses_offset = Array{Loss}(n)
D = 0
for i=1:n
    options = unique(all_data_offset[:, i])
    #num_options = maximum(options)
    num_options = max(maximum(options), 3)
    losses_offset[i] = BvSLoss(num_options)
    D += (num_options-1)
end
@show m, n, D

# construct the model
rx, ry = SimplexConstraint(), QuadReg(.01)
Yord = randn(k,D)
yidxs = get_yidxs(losses_offset)
for j=1:n
    prox!(ry, view(Yord,:,yidxs[j]), 1)
end
glrm = GLRM(all_data_offset, losses_offset, rx, ry, k, obs=obs, scale=false, offset=false, X=randn(k, m), Y=Yord);

# cross validate
params = ProxGradParams(max_iter=500)
train_error, test_error, train_glrms, test_glrms = cross_validate(glrm, nfolds=nfolds, params=params)

write to file
writecsv(string(data_directory, "/impute_bvs_simplex_cv_train_error$(k).csv"), train_error)
writecsv(string(data_directory, "/impute_bvs_simplex_cv_test_error$(k).csv"), test_error)

# fit
@time X,Y,ch = fit!(glrm, ProxGradParams(max_iter=500));

# write to file
A_imputed = impute(glrm)
writecsv(string(data_directory, "/impute_bvs_simplex_initk_X$(k).csv"), X)
writecsv(string(data_directory, "/impute_bvs_simplex_initk_Y$(k).csv"), Y)
writecsv(string(data_directory, "/impute_bvs_simplex_initk_Z$(k).csv"), A_imputed)

