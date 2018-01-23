using DataFrames
using LowRankModels


# Pull command line arguments
data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
@show data_directory, k

# Read in training data
df = readtable(string(data_directory, "/all_samples_filtered_train.csv"), header=false)
train_data = sparse(Array(df))

# Read in entry test data
df = readtable(string(data_directory, "/all_samples_filtered_entry_test.csv"), header=false)
entry_test_data = sparse(Array(df))

# Read in instrument test data
df = readtable(string(data_directory, "/all_samples_filtered_instrument_test.csv"), header=false)
instrument_test_data = sparse(Array(df))

# Regroup all data (0 means missing, so we can just add)
all_data = train_data + entry_test_data + instrument_test_data
m, n = size(all_data)
dropzeros!(all_data)

# Offset values so that 0 indicates missing and all other entries are 1, 2, 3, etc
all_data[all_data .> 0] = all_data[all_data .> 0] + 1
all_data[all_data.==-1] = 1

# Pull observed (nonzero) entries
i, j, v = findnz(all_data)
obs = collect(zip(i, j))

@show maximum(all_data), minimum(all_data), size(obs, 1)

# construct the model
rx, ry = SimplexConstraint(), QuadReg(.01)

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

glrm = GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=true, X=Xinit, Y=Yord);

# fit full model
@time X,Y,ch = fit!(glrm, ProxGradParams(max_iter=500));

# write to file
writecsv(string(data_directory, "/impute_bvs_simplex_offset_full_X$(k).csv"), X)
writecsv(string(data_directory, "/impute_bvs_simplex_offset_full_Y$(k).csv"), Y)
writecsv(string(data_directory, "/impute_bvs_simplex_offset_full_Z$(k).csv"), impute(glrm))


