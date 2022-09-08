#!/bin/bash

DIR=$(cd "$(dirname "$0")"; pwd)

FILELIST_DIR=$DIR/filelists

if [ ! -d $FILELIST_DIR ]; then
    echo "Could not find file lists at $FILELIST_DIR"
    echo "Run generate_filelists.sh first"
    exit 1
fi

TASK_DIR=$DIR/tasks

echo "Cleaning task dir at $TASK_DIR"
mkdir -p $TASK_DIR
rm $TASK_DIR/*

echo "Launching conversions"
bsub -P scicompsoft -n 1 -J "matches[1-45]" -e "$TASK_DIR/stderr.%I" -o "$TASK_DIR/stdout.%I" "$DIR/convert.sh $FILELIST_DIR/filelist_\$LSB_JOBINDEX.txt"

