#!/bin/bash

export DSPACE_PPPL_HOME=$HOME/pulibrary-src/dspace-python/pppl
export DSPACE_AWS_S3=$DSPACE_PPPL_HOME/s3
export AWS_BUCKET=pppldataspace

echo "aws s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports"
aws s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports
