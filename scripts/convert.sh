#!/bin/bash

DIR=$(cd "$(dirname "$0")"; pwd)
BASEDIR=$(realpath $DIR/..)

cd $BASEDIR

eval "$(conda shell.bash hook)"
conda activate neuronbridge-python

echo "./neuronbridge/upgrade_model.py -m $1"
./neuronbridge/upgrade_model.py -m $1

