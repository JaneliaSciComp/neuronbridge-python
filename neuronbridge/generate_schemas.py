from neuronbridge.model import *
from pathlib import Path

def print_schemas():
    for model in [EMImageLookup, LMImageLookup, PPPMatches, CDSMatches]:
        print(model.schema_json(indent=2))
        print()

def write_schemas():
    ROOT_DIR = "schemas"
    for model in [EMImageLookup, LMImageLookup, PPPMatches, CDSMatches]:
        filepath = Path(ROOT_DIR) / f"{model.__name__}.json"
        with open(filepath, 'w') as f:
            f.write(model.schema_json(indent=2))
            f.write('\n')

if __name__ == '__main__':
    write_schemas()