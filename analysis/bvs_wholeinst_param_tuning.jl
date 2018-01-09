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

# Breaks samples into folds
function getfolds(samples::Array{Int,1}, nfolds)
    # partition elements of samples into nfolds groups
    groups = Array{Int}(size(samples))
    rand!(groups, 1:nfolds)  # fill an array with random 1 through N
    # create the training and testing observations for each fold
    folds = Array{Tuple}(nfolds)
    for ifold=1:nfolds
        train = samples[filter(i->groups[i]!=ifold, 1:length(samples))] # all the samples that didn't get the ifold label
        test = samples[filter(i->groups[i]==ifold, 1:length(samples))] # all the obs that did
        folds[ifold] = (train, test)
    end
    return folds
end

# Features fo each instrument
adir_indices = 1:139
ados_indices = 140:185
srs_indices = 186:250

# Find samples with all three instruments
have_all_three = []
for i=1:m
    has_adir = sum(all_data[i, adir_indices]) > 0
    has_ados = sum(all_data[i, ados_indices]) > 0
    has_srs = sum(all_data[i, srs_indices]) > 0
    if has_adir & has_ados & has_srs
        push!(have_all_three, i)
    end
end

train_error = Array{Float64}(nfolds)
test_error = Array{Float64}(nfolds)
    
folds = getfolds(Array{Int}(have_all_three), nfolds)
for ifold=1:nfolds
    println("\nforming train and test GLRM for fold $ifold")

    # Select train/test samples for this fold
    train_samples, test_samples = folds[ifold]
    ntrain = length(train_samples)
    ntest = length(test_samples)

    # Now select adir/ados/srs samples from the test samples
    instrument_folds = getfolds(test_samples, 3)

    # Mask instruments
    train_data = copy(all_data)
    test_data = zeros(all_data)

    # Mask entries
    test_data[instrument_folds[1][2], adir_indices] = train_data[instrument_folds[1][2], adir_indices]
    train_data[instrument_folds[1][2], adir_indices] = 0
    test_data[instrument_folds[2][2], ados_indices] = train_data[instrument_folds[2][2], ados_indices]
    train_data[instrument_folds[2][2], ados_indices] = 0
    test_data[instrument_folds[3][2], srs_indices] = train_data[instrument_folds[3][2], srs_indices]
    train_data[instrument_folds[3][2], srs_indices] = 0
    dropzeros!(train_data)

    # Mask obs
    is, js, vs = findnz(train_data)
    obs = collect(zip(is, js))

    test_data = sparse(test_data)
    dropzeros!(test_data)

    is, js, vs = findnz(test_data)
    test_obs = collect(zip(is, js))

    println("training model on $ntrain samples and testing on $ntest")
    println(size(nonzeros(train_data), 1))
    println(size(nonzeros(test_data), 1))

    # Initialize X and Y
	Xinit = randn(k, m)
	Yord = randn(k, D)
	yidxs = get_yidxs(losses)
	for j=1:n
	    prox!(ry, view(Yord,:,yidxs[j]), 1)
	end

	# Fit model
    train_glrm = GLRM(train_data, losses, rx, ry, k, obs=obs, scale=false, offset=true, X=Xinit, Y=Yord);
    X,Y,ch = LowRankModels.fit!(train_glrm, params=ProxGradParams(max_iter=500), verbose=true);

    train_error[ifold] = objective(train_glrm,
            X, Y, include_regularization=false) / size(nonzeros(train_data), 1)
    println("\ttrain error: $(train_error[ifold])")

    test_glrm = GLRM(test_data, losses, rx, ry, k, obs=test_obs, scale=false, offset=false, X=Xinit, Y=Yord)
    test_error[ifold] = objective(test_glrm,
            X, Y, include_regularization=false) / size(nonzeros(test_data), 1)
    println("\ttest error:  $(test_error[ifold])")
    
    # write to file
	writecsv(string(data_directory, "/impute_bvs_simplex_offset_cv_train_error_wholeinst$(k).csv"), train_error)
	writecsv(string(data_directory, "/impute_bvs_simplex_offset_cv_test_error_wholeinst$(k).csv"), test_error)    
end
    
