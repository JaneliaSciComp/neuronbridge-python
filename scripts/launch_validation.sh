#!/bin/bash
bsub -P scicompsoft -o std%J.out -e std%J.out -n 20 -R "span[ptile=4]" bash -i $PWD/../ray-integration/ray_cluster.sh -c "python $PWD/neuronbridge/validate_ray.py --nomatches" -n "neuronbridge-python" -m 20000000000

