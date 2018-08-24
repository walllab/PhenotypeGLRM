using LowRankModels
println("LowRankModels loaded")
flush(STDOUT)

# Pull command line arguments
data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
fold = parse(Int64, ARGS[3])
@show data_directory, k, fold
println("Command line arguments loaded")
flush(STDOUT)

function read_data(filename, gendiag_filename, map_filename)
	println("Read in data ", filename)
	# Read in training data
	all_data = readcsv(filename, Int, header=false)
	#all_data = vcat(all_data[1:100, :], all_data[end-100:end, :])

	# read in gender and diagnosis data
	gendiag = readcsv(gendiag_filename, header=false)
	#gendiag = vcat(gendiag[1:100, :], gendiag[end-100:end, :])

	# Form sparse array
	all_data = sparse(Array(all_data))
	dropzeros!(all_data)

	# Pull observed (nonzero) entries
	i, j, v = findnz(all_data)
	obs = collect(zip(i, j))
	@show maximum(all_data), minimum(all_data), size(obs, 1)

	num_options = readdlm(map_filename, '\t', header=false)[(size(all_data, 2)+1):(2*(size(all_data, 2)))]

	println("Data loaded")
	flush(STDOUT)
	return all_data, obs, num_options, gendiag
end

function build_model(all_data, obs, k, num_options, gendiag)
	m, n = size(all_data)
	rx = Array{Regularizer}(m)
	ry = QuadReg(.01)
	

	# Latent features
	last_diag = findlast(gendiag[:, 2])
	for i=1:last_diag
		rx[i] = fixed_latent_features(QuadReg(0.01), gendiag[i, :])
	end
	for i=(last_diag+1):m
		rx[i] = fixed_latent_features(QuadReg(0.01), gendiag[i, 1:1], 1)
	end

	# construct the Loss
	losses = Array{Loss}(n)
	D = 0
	for i=1:n
		if num_options[i] == 2
			losses[i] = LogisticLoss()
			D += 1
		else
	    	losses[i] = MultinomialLoss(num_options[i])
	    	D += num_options[i]
	    end
	end
	@show m, n, D

	# Initialize X and Y
	Xinit = randn(k, m)
	Yinit = randn(k, D)
	yidxs = get_yidxs(losses)
	for i=1:n
	    prox!(ry, view(Yinit,:,yidxs[i]), 1)
	end

	println("Model built")
    flush(STDOUT)
	return GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=true, X=Xinit, Y=Yinit)
end

function run_model(fold, k)
	all_data, obs, num_options, gendiag = @time read_data(string(data_directory, "/all_samples_ordinal_gender_cv$(fold)_train.csv"),
									string(data_directory, "/all_samples_ordinal_cleaned_gender_gendiag.csv"),
									string(data_directory, "/all_samples_ordinal_cleaned_map.txt"))

	glrm = @time build_model(all_data, obs, k, num_options, gendiag)

	# Fit model
    X,Y,ch = @time LowRankModels.fit!(glrm, params=ProxGradParams(max_iter=500), verbose=true);
    println("Model trained")
    flush(STDOUT)

	@time writecsv(string(data_directory, "/impute_mult_gender_cv_k$(k)_fold$(fold).csv"), impute(glrm))
	@time writecsv(string(data_directory, "/impute_mult_gender_X_cv_k$(k)_fold$(fold).csv"), X)
	@time writecsv(string(data_directory, "/impute_mult_gender_Y_cv_k$(k)_fold$(fold).csv"), Y)

	println("Model saved")
    flush(STDOUT)
end

run_model(fold, k)

