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
	m, n = size(df)

	# Form sparse array
	all_data = sparse(Array(df))
	dropzeros!(all_data)
	p = size(nonzeros(all_data), 1)

	# Pull observed (nonzero) entries
	i, j, v = findnz(all_data)
	obs = collect(zip(i, j))
	@show maximum(all_data), minimum(all_data), size(obs, 1)

	# construct the model
	rx, ry, losses = QuadReg(0.01), QuadReg(0.01), QuadLoss()

	glrm = GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=true)

	# Fit model
    X,Y,ch = LowRankModels.fit!(glrm, params=ProxGradParams(max_iter=500), verbose=true)
	writecsv(string(data_directory, "/impute_quad_cv_k$(k)_fold$(fold).csv"), impute(glrm))
end