#!/bin/bash

DIR=$(cd "$(dirname "$0")"; pwd)

cd $DIR

eval "$(conda shell.bash hook)"
conda activate neuronbridge-python

FILELIST_DIR=$DIR/filelists
echo "Cleaning filelists dir at $FILELIST_DIR"
mkdir -p $FILELIST_DIR
rm $FILELIST_DIR/*

echo "Running ./neuronbridge/upgrade_model.py --filelists"
../neuronbridge/upgrade_model.py --filelists

echo "Ready to run submit.sh"

