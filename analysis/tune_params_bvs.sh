#!/bin/bash
#
#
#SBATCH --job-name=bvs
#SBATCH --output=bvs%A_%a.out
#SBATCH --error=bvs%A_%a.err
#SBATCH --array=5-9
#SBATCH -p dpwall
#SBATCH -D /scratch/PI/dpwall/DATA/iHART/kpaskov/PhenotypeGLRM
#SBATCH -t 20:00:00

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID is " $SLURM_ARRAY_TASK_ID

module load julia/0.6.4
julia analysis/tune_params_bvs.jl data $1 $SLURM_ARRAY_TASK_ID
