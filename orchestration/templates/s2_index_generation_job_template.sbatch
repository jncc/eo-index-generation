#!/bin/bash
#SBATCH --account defra_eo
#SBATCH --qos high
#SBATCH --partition standard
#SBATCH --cpus-per-task=$cpuCount
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH -D $jobWorkingDir
#SBATCH -o $jobWorkingDir/%J.out
#SBATCH -e $jobWorkingDir/%J.err

/usr/bin/singularity exec --bind /neodc/sentinel_ard/data,/datacentre --bind $inputMount:/input --bind $outputMount:/output --bind $stateMount:/state --bind $workingMount:/working --bind $tmpMount:/tmp $containerPath /app/exec.sh --module workflow.processing CopyIndicesCogsToOutputForS2 --productId $productId $indices --workers $cpuCount --local-scheduler

if [ -f $stateMount/CopyIndicesCogsToOutputForS2.json ]; then
    rm -r $workingMount/*
    rm $inputMount/$productId*
fi
