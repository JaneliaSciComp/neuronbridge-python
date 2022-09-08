#!/bin/bash

DIR=$(cd "$(dirname "$0")"; pwd)
BASEDIR=$(realpath $DIR/..)

bsub -P scicompsoft -o std%J.out -e std%J.out -n 20 -R "span[ptile=4]" bash -i $BASEDIR/../ray-integration/ray_cluster.sh -c "python $BASEDIR/neuronbridge/validate_ray.py --nomatches" -n "neuronbridge-python" -m 20000000000

