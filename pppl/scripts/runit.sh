#!/bin/bash

export DATASPACE_IMPORT=$DSPACE_PPPL_HOME/dataspace_import.py
export S3_LOGDIR=$DSPACE_AWS_S3/log
export DATE=`date "+%Y/%m"`
export LONG_DATE=`date "+%Y-%m-%d:%H:%M"`
export IMPORT_LOG_DIR=$S3_LOGDIR/$DATE
export IMPORT_LOG_FILE=$IMPORT_LOG_DIR/$LONG_DATE-s3-bucket.log

mkdir -p $IMPORT_LOG_DIR
touch $IMPORT_LOG_FILE

echo  "Logging to $IMPORT_LOG_FILE"
echo "aws s3 sync s3://$AWS_BUCKET $DSPACE_AWS_S3 >> $IMPORT_LOG_FILE"
aws s3 sync s3://$AWS_BUCKET $DSPACE_AWS_S3 >> $IMPORT_LOG_FILE

fgrep 'Download:' $IMPORT_LOG_FILE >> /dev/null
if [ $? == 0 ]; then
  echo "python $DATASPACE_IMPORT $DSPACE_AWS_S3 $DSPACE_EPERSON >> $IMPORT_LOG_FILE"
  python $DATASPACE_IMPORT $DSPACE_AWS_S3 $DSPACE_EPERSON >> $IMPORT_LOG_FILE
fi

fgrep 'Download failed:' $IMPORT_LOG_FILE >> /dev/null
if [[ $status -eq 0 ]]; then
  echo "FAILURE to sync s3 bucket" >> $IMPORT_LOG_FILE
fi

echo "aws s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports >> $IMPORT_LOG_FILE"
aws s3 sync $DSPACE_AWS_S3/imports s3://$AWS_BUCKET/imports >> $IMPORT_LOG_FILE

if [ -e $IMPORT_LOG_FILE ]; then
  echo "$IMPORT_LOG_FILE is empty - deleting"
  rm $IMPORT_LOG_FILE
else
  echo "aws s3 sync $DSPACE_AWS_S3/log s3://$AWS_BUCKET/log"
  aws s3 sync $DSPACE_AWS_S3/log s3://$AWS_BUCKET/log
  echo "---"
  cat $IMPORT_LOG_FILE
fi
