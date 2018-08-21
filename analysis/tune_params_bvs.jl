using LowRankModels

# Pull command line arguments
data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
nfolds = parse(Int64, ARGS[3])
@show data_directory, k, nfolds

for fold=0:nfolds
	# Read in training data
	all_data = readcsv(string(data_directory, "/all_samples_ordinal_cv$(fold)_train.csv"), Int, header=false)
	#all_data = readcsv(string(data_directory, "/all_samples_ordinal_test_train.csv"), Int, header=false)[1:100, :]
	m, n = size(all_data)

	# Form sparse array
	all_data = sparse(Array(all_data))
	dropzeros!(all_data)
	p = size(nonzeros(all_data), 1)

	# Pull observed (nonzero) entries
	i, j, v = findnz(all_data)
	obs = collect(zip(i, j))
	@show maximum(all_data), minimum(all_data), size(obs, 1)

	# construct the model
	rx, ry = QuadReg(0.01), QuadReg(0.01)

	# construct the BVSLoss
	losses = Array{Loss}(n)
	D = 0
	for i=1:n
	    options = unique(all_data[:, i])
		num_options = max(maximum(options), 3)
	    losses[i] = BvSLoss(num_options)
	    D += (num_options-1)
	end
	@show m, n, D

	# Initialize X and Y
	Xinit = randn(k, m)
	Yord = randn(k, D)
	yidxs = get_yidxs(losses)
	for i=1:n
	    prox!(ry, view(Yord,:,yidxs[i]), 1)
	end

	glrm = GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=true, X=Xinit, Y=Yord);

	# Fit model
    X,Y,ch = LowRankModels.fit!(glrm, params=ProxGradParams(max_iter=500), verbose=true);
	writecsv(string(data_directory, "/impute_bvs_cv_k$(k)_fold$(fold).csv"), impute(glrm))
end