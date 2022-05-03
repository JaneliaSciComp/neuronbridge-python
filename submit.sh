#!/bin/bash
DIR=/groups/scicompsoft/home/rokickik/dev/neuronbridge-python
TASK_DIR=$DIR/tasks
FILELIST_DIR=$DIR/filelists
bsub -P scicompsoft -n 1 -J "matches[1-45]" -e "$TASK_DIR/stderr.%I" -o "$TASK_DIR/stdout.%I" "$DIR/convert.sh $FILELIST_DIR/filelist_\$LSB_JOBINDEX.txt"

