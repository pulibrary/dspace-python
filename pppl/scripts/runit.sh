#!/bin/bash

if [ -z "$DSPACE_PPPL_HOME" ]; then
  echo '$DSPACE_PPPL_HOME needs to be declared'
  exit 1
fi
if [ -z "$DSPACE_AWS_S3" ]; then
  echo '$DSPACE_AWS_S3 needs to be declared'
  exit 1
fi
if [ -z "$AWS_BUCKET" ]; then
  echo '$AWS_BUCKET needs to be declared'
  exit 1
fi
if [ -z "$DSPACE_EPERSON" ]; then
  echo '$DSPACE_EPERSON needs to be declared'
  exit 1
fi

export DATASPACE_IMPORT=$DSPACE_PPPL_HOME/dataspace_import.py

export S3_LOGDIR=$DSPACE_AWS_S3/log
export DATE=`date "+%Y/%m"`
export LONG_DATE=`date "+%Y-%m-%d:%H:%M"`
export IMPORT_LOG_DIR=$S3_LOGDIR/$DATE
export IMPORT_LOG_FILE=$IMPORT_LOG_DIR/$LONG_DATE-s3-bucket.log

mkdir -p $IMPORT_LOG_DIR
touch $IMPORT_LOG_FILE

# This synchronizes from S3 to the local file system
echo  "Logging to $IMPORT_LOG_FILE"
echo "aws --debug s3 sync s3://$AWS_BUCKET $DSPACE_AWS_S3 >> $IMPORT_LOG_FILE"
aws --debug s3 sync s3://$AWS_BUCKET $DSPACE_AWS_S3 >> $IMPORT_LOG_FILE

# This uploads any new SIPs
echo "python $DATASPACE_IMPORT $DSPACE_AWS_S3 $DSPACE_EPERSON >> $IMPORT_LOG_FILE"
python $DATASPACE_IMPORT $DSPACE_AWS_S3 $DSPACE_EPERSON >> $IMPORT_LOG_FILE

# This synchronizes from the local file system to S3
echo "aws --debug s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports >> $IMPORT_LOG_FILE"
aws --debug s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports >> $IMPORT_LOG_FILE

if [ -e $IMPORT_LOG_FILE ]; then
  echo "Warning: $IMPORT_LOG_FILE is empty"
else
  echo "aws --debug s3 sync $DSPACE_AWS_S3/log s3://$AWS_BUCKET/log"
  aws --debug s3 sync $DSPACE_AWS_S3/log s3://$AWS_BUCKET/log
  echo "---"
  cat $IMPORT_LOG_FILE
fi
