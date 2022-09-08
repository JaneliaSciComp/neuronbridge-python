#!/bin/bash

DIR=$(cd "$(dirname "$0")"; pwd)

cd $DIR

eval "$(conda shell.bash hook)"
conda activate neuronbridge-python

echo "Running ./neuronbridge/upgrade_model.py --filelists"
../neuronbridge/upgrade_model.py --filelists

echo "Ready to run submit.sh"

