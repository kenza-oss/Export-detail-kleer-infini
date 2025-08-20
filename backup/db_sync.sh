#!/bin/bash

# Set your AWS CLI path (update with your actual path if needed)
AWS_CLI_PATH="/usr/local/bin/aws"

# Set your Amazon S3 bucket name
S3_BUCKET="my-bucket-name"

# Specify the source directory where your backups are stored
SOURCE_DIR="~/db_backups"

# Synchronize the backups with Amazon S3
$AWS_CLI_PATH s3 sync $SOURCE_DIR s3://$S3_BUCKET
