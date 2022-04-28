#!/usr/bin/env python
import json
from devtools import debug
import neuronbridge.legacy_model as legacy_model
import neuronbridge.model as model

VNC_ALIGNMENT_SPACE = "JRC2018_VNC_Unisex_40x_DS"
BRAIN_ALIGNMENT_SPACE = "JRC2018_Unisex_20x_HR"


def upgrade_em_lookup(em_lookup : legacy_model.EMImageLookup):

    lookup = model.EMImageLookup()
    lookup.results = []

    for em_lookup in em_lookup.results:
        em_image = model.EMImage()
        em_image.id = em_lookup.id
        em_image.libraryName = em_lookup.libraryName
        em_image.publishedName = em_lookup.publishedName
        em_image.gender = em_lookup.gender
        em_image.alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in em_lookup.imageURL else BRAIN_ALIGNMENT_SPACE
        
        em_image.neuronType = em_lookup.neuronType
        em_image.neuronInstance = em_lookup.neuronInstance
        lookup.results.append(em_image)
        



with open("test_data/em-body.json") as f:
    obj = upgrade_em_lookup(legacy_model.EMImageLookup(**json.load(f)))
    debug(obj.results[0])

with open("test_data/em-body-vnc.json") as f:
    obj = upgrade_em_lookup(legacy_model.EMImageLookup(**json.load(f)))
    debug(obj.results[0])

# with open("test_data/mcfo-line.json") as f:
#     obj = legacy_model.LMImageLookup(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/mcfo-line-vnc.json") as f:
#     obj = legacy_model.LMImageLookup(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/flyem-flylight-vnc.json") as f:
#     obj = legacy_model.CDSMatches(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/flyem-flylight.json") as f:
#     obj = legacy_model.CDSMatches(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/flylight-flyem-vnc.json") as f:
#     obj = legacy_model.CDSMatches(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/flylight-flyem.json") as f:
#     obj = legacy_model.CDSMatches(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/pppresult-vnc.json") as f:
#     obj = legacy_model.PPPMatches(**json.load(f))
#     debug(obj.results[0])

# with open("test_data/pppresult.json") as f:
#     obj = legacy_model.PPPMatches(**json.load(f))
#     debug(obj.results[0])


