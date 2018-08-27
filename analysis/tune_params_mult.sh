#!/bin/bash
#
#
#SBATCH --job-name=mult
#SBATCH --output=mult%A_%a.out
#SBATCH --error=mult%A_%a.err
#SBATCH --array=5-9
#SBATCH -p dpwall
#SBATCH -D /scratch/PI/dpwall/DATA/iHART/kpaskov/PhenotypeGLRM
#SBATCH -t 20:00:00

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID is " $SLURM_ARRAY_TASK_ID

module load julia/0.6.4
julia analysis/tune_params_mult.jl data $1 $SLURM_ARRAY_TASK_ID
