using LowRankModels
println("LowRankModels loaded")
flush(STDOUT)

# Pull command line arguments
data_directory = ARGS[1]
k = parse(Int64, ARGS[2])
fold = parse(Int64, ARGS[3])
instrument = ARGS[4]
@show data_directory, k, fold, instrument
println("Command line arguments loaded")
flush(STDOUT)

function read_data(filename, map_filename)
	println("Read in data ", filename)
	# Read in training data
	all_data = readcsv(filename, Int, header=false)
	all_data = all_data[1:100, :]

	# Pull number of options for each item
	num_options = readdlm(map_filename, '\t', header=false)[(size(all_data, 2)+1):(2*(size(all_data, 2)))]

	if instrument != "all"
		from_inst = Array([startswith(x, instrument) for x in readdlm(map_filename, '\t', header=false)[1:size(all_data, 2)]])
		print(from_inst)
		println(size(from_inst), size(all_data))
		all_data = [:, from_inst]
		num_options = num_options[from_inst]
	end

	# Form sparse array
	all_data = sparse(Array(all_data))
	dropzeros!(all_data)

	# Pull observed (nonzero) entries
	i, j, v = findnz(all_data)
	obs = collect(zip(i, j))
	@show size(all_data)
	@show maximum(all_data), minimum(all_data), size(obs, 1)

	println("Data loaded")
	flush(STDOUT)
	return all_data, obs, num_options
end

function build_model(all_data, obs, k, num_options)
	m, n = size(all_data)
	rx, ry = QuadReg(0.01), QuadReg(0.01)
	#rx, ry = lastentry1(QuadReg(.01)), OrdinalReg(QuadReg(.01))

	# construct the BVSLoss
	losses = Array{Loss}(n)
	D = 0
	for i=1:n
		if num_options[i] == 2
			losses[i] = LogisticLoss()
			D += 1
		else
	    	losses[i] = BvSLoss(num_options[i])
	    	D += (num_options[i]-1)
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
	return GLRM(all_data, losses, rx, ry, k, obs=obs, scale=false, offset=false, X=Xinit, Y=Yinit)
end

function run_model(fold, k)
	all_data, obs, num_options = @time read_data(string(data_directory, "/all_samples_ordinal_cv$(fold)_train.csv"),
									string(data_directory, "/all_samples_ordinal_cleaned_map.txt"))

	glrm = @time build_model(all_data, obs, k, num_options)

	# Fit model
    X,Y,ch = @time LowRankModels.fit!(glrm, params=ProxGradParams(max_iter=500), verbose=true);
    println("Model trained")
    flush(STDOUT)

	@time writecsv(string(data_directory, "/impute_bvs_cv_k$(k)_fold$(fold).csv"), impute(glrm))
	@time writecsv(string(data_directory, "/impute_bvs_X_cv_k$(k)_fold$(fold).csv"), X)
	@time writecsv(string(data_directory, "/impute_bvs_Y_cv_k$(k)_fold$(fold).csv"), Y)
	
	println("Model saved")
    flush(STDOUT)
end

run_model(fold, k)

