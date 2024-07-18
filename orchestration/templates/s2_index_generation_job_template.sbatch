#!/bin/bash
#SBATCH -p par-single
#SBATCH -n 3
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH -D $jobWorkingDir
#SBATCH -o $jobWorkingDir/%J.out
#SBATCH -e $jobWorkingDir/%J.err

/usr/bin/singularity exec --bind /neodc/sentinel_ard/data,/datacentre $cloudMaskBasePath --bind $inputMount:/input --bind $outputMount:/output --bind $stateMount:/state --bind $workingMount:/working --bind $tmpMount:/tmp $containerPath /app/exec.sh --module workflow.processing ValidateIndicesForS2 --productId $productId $indices --local-scheduler

if [ -f $stateMount/ValidateIndicesForS2.json ]; then
    rm -r $workingMount/*
fi
