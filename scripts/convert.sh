#!/bin/bash

cd /groups/scicompsoft/home/rokickik/dev/neuronbridge-python/
eval "$(conda shell.bash hook)"
conda activate neuronbridge-python
echo "./neuronbridge/upgrade_model.py -m $1"
./neuronbridge/upgrade_model.py -m $1

