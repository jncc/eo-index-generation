#!/bin/bash
# Vars
# $MAJOR_VERSION : defined in build config
# $APPTAINER_VERSION : defined in build config
# $WORKSPACE : Workspace path defined by jenkins 

# Jenkins container build script

# Create tag
if [[ $GIT_BRANCH == *main ]] 
then
  TAG=$MAJOR_VERSION.$BUILD_NUMBER;
else
  TAG="test";
fi

# Build the docker image
docker build -t jncc/habitat-change-detection-workflow:$TAG $WORKSPACE/container/

# Build apptainer image
cd /data/apptainer-images && apptainer build --force habitat-change-detection-workflow-$TAG.sif docker-daemon://jncc/habitat-change-detection-workflow:$TAG

# Push apptainer image to S3 jncc-dist bucket
aws s3 cp /data/apptainer-images/habitat-change-detection-workflow-$TAG.sif s3://jncc-dist/habitat-change-detection-workflow/apptainer/

docker rmi jncc/habitat-change-detection-workflow:$TAG

# Remove temp files
rm -f /data/apptainer-images/habitat-change-detection-workflow-$TAG.sif

# Create a presigned url to allow access for 12 hours
echo "Generating URL for download which will expire in 12 hours..."
aws s3 presign s3://jncc-dist/habitat-change-detection-workflow/apptainer/habitat-change-detection-workflow-$TAG.sif --expires-in 43200