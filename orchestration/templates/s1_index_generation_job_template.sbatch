#!/bin/bash
#SBATCH --account defra_eo
#SBATCH --partition standard
#SBATCH --qos short
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH -D $jobWorkingDir
#SBATCH -o $jobWorkingDir/%J.out
#SBATCH -e $jobWorkingDir/%J.err

/usr/bin/singularity exec --bind /neodc/sentinel_ard/data,/datacentre --bind $inputMount:/input --bind $outputMount:/output --bind $stateMount:/state --bind $workingMount:/working --bind $tmpMount:/tmp $containerPath /app/exec.sh --module workflow.processing CopyIndicesCogsToOutputForS1 --productId $productId $indices --local-scheduler

if [ -f $stateMount/CopyIndicesCogsToOutputForS1.json ]; then
    rm -r $workingMount/*
    rm $inputMount/$productId*
fi
