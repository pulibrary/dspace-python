#!/bin/bash

# . cronrc

export DSPACE_PPPL_HOME=$HOME/pulibrary-src/pppl
export DSPACE_AWS_S3=$DSPACE_PPPL_HOME/s3
export AWS_BUCKET=pppldataspace

export DSPACE_EPERSON="pppldataspace@princeton.edu"
export ERROR_EMAIL_TO="jrg5@princeton.edu"
export LOG_LEVEL=DEBUG

source $DSPACE_PPPL_HOME/scripts/runit.sh
if [ "$?" != 0 ]; then
  echo 'fail'
  mutt -s 'dataspace import of pppl package failed' $ERROR_EMAIL_TO  <<- EOM
    script ran on $(hostname)
    see dated log file in s3://$AWS_BUCKET/log
EOM

fi
