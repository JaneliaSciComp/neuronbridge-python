# How to run the upgrade scripts

There are temporary scripts available on this branch (DataModel3) which convert from the previous
model versions (2.4.0 for Brain and 2.3.0-pre for VNC) into a new consolidated version (3.0.0-alpha). These scripts (and this documentation) will never be merged into the main branch.

For the scripts to work, you should first create a conda environment with a specific name:

    conda env create -f environment.yml
    conda activate neuronbridge-python

Now you should be able to do the following tasks...

## Regenerate the image metadata (i.e. by_body, by_line JSONs)

**Warning: this writes to /nrs/neuronbridge/v3.0.0-alpha**

    ./neuronbridge/upgrade_model.py --allimages

## Regenerate the matches

This requires a few steps:

### Load images into a temporary database cache

In order to convert the matches, images must be in the database. This script will walk you through deleting the existing temporary table and recreating the indexes on it when its done.

    ./neuronbridge/upgrade_model.py --allimagestodb

### Generate file lists

    ./scripts/generate_filelists.sh

### Launch conversion on the cluster

    ./scripts/submit.sh

You can monitor the output under ./scripts/tasks
