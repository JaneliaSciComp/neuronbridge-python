#!/usr/bin/env python

import json
from pathlib import Path

from neuronbridge.model import *

ROOT_DIR = "schemas"

def print_schemas():
    for model in [DataConfig, ImageLookup, Matches]:
        print(model.schema_json(indent=2))
        print()

def write_schema(schema_name, schema_obj):
    filepath = Path(ROOT_DIR) / f"{schema_name}.json"
    with open(filepath, 'w') as f:
        f.write(schema_obj.schema_json(indent=2))
        f.write('\n')


def write_schemas():

    write_schema("DataConfig", DataConfig)
    write_schema("ImageLookup", ImageLookup)
    write_schema("PrecomputedMatches", PrecomputedMatches)
    write_schema("CustomMatches", CustomMatches)


if __name__ == '__main__':
    write_schemas()