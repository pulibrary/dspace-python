#!/bin/bash

# . cronrc

export DSPACE_PPPL_HOME=$HOME/pulibrary-src/dspace-python/pppl
export DSPACE_AWS_S3=$DSPACE_PPPL_HOME/s3
export AWS_BUCKET=pppldataspace
export DSPACE_EPERSON="pppldataspace@princeton.edu"

export DSPACE_PPPL_EMAIL="jrg5@princeton.edu"
export LOG_LEVEL=DEBUG

source $DSPACE_PPPL_HOME/scripts/runit.sh
if [ "$?" != 0 ]; then
  echo 'fail'
  mutt -s 'dataspace import of pppl package failed' $DSPACE_PPPL_EMAIL  <<- EOM
    script ran on $(hostname)
    see dated log file in s3://$AWS_BUCKET/log
EOM

fi
