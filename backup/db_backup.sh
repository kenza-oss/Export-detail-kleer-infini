#!/bin/bash
DIR=`date +%d-%m-%y`
DEST=~/db_backups/$DIR
mkdir $DEST

PGPASSWORD='postgres_password' pg_dump --inserts --column-inserts --username=postgres_user --host=postgres_host --port=postgres_port postgres_database_name > dbbackup.sql
