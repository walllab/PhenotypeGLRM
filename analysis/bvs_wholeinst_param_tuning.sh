#!/bin/bash
#
#
#SBATCH --job-name=wi_param_tuning
#SBATCH --output=wi_param_tuning%A_%a.out
#SBATCH --error=wi_param_tuning%A_%a.err
#SBATCH --array=1-15
#SBATCH -p dpwall
#SBATCH -D /scratch/PI/dpwall/DATA/iHART/kpaskov/PhenotypeGLRM
#SBATCH -t 20:00:00
#SBATCH --mem=8G

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID is " $SLURM_ARRAY_TASK_ID

/scratch/PI/dpwall/DATA/iHART/kpaskov/julia-d386e40c17/bin/julia /scratch/PI/dpwall/DATA/iHART/kpaskov/PhenotypeGLRM/analysis/bvs_wholeinst_param_tuning.jl /scratch/PI/dpwall/DATA/iHART/kpaskov/PhenotypeGLRM/data $SLURM_ARRAY_TASK_ID 5
