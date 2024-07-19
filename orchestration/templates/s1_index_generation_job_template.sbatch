#!/bin/bash
#SBATCH -p par-single
#SBATCH -n $indexCount
#SBATCH -N 1
#SBATCH --time=04:00:00
#SBATCH --mem=72G
#SBATCH -D $jobWorkingDir
#SBATCH -o $jobWorkingDir/%J.out
#SBATCH -e $jobWorkingDir/%J.err

/usr/bin/singularity exec --bind /neodc/sentinel_ard/data,/datacentre --bind $inputMount:/input --bind $outputMount:/output --bind $stateMount:/state --bind $workingMount:/working --bind $tmpMount:/tmp $containerPath /app/exec.sh --module workflow.processing PrepareProcessing --productId $productId --local-scheduler

memPerCpu=$$((72 / $indexCount))
indices=$indices

for index in "$${indices[@]}"
do
    mkdir -p $stateMount/$$index
    cp $stateMount/PrepareProcessing.json $stateMount/$$index/PrepareProcessing.json
    srun -n1 -N1 --exclusive --mem-per-cpu=$${memPerCpu}G /usr/bin/singularity exec --bind /neodc/sentinel_ard/data,/datacentre --bind $inputMount:/input --bind $outputMount:/output --bind $stateMount/$$index:/state --bind $workingMount:/working --bind $tmpMount:/tmp $containerPath /app/exec.sh --module workflow.processing ValidateIndicesForS1 --productId $productId --indices $$index --local-scheduler &
done
wait
