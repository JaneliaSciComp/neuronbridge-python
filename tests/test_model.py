import json

from neuronbridge.model import *
from neuronbridge.model import PPPMatch
from neuronbridge.model import LMImage

by_body = json.loads(
"""
{
  "results" : [ {
    "libraryName" : "FlyEM_Hemibrain_v1.2.1",
    "alignmentSpace" : "JRC2018_Unisex_20x_HR",
    "anatomicalArea" : "Brain",
    "gender" : "f",
    "neuronType" : "ORN_DA1",
    "neuronInstance" : "ORN_DA1_L",
    "id" : "2945073143148142603",
    "publishedName" : "hemibrain:v1.2.1:1734696429",
    "files" : {
      "AlignedBodyOBJ" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/OBJ/1734696429.obj",
      "CDM" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.png",
      "store" : "fl:open_data:brain",
      "CDMThumbnail" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.jpg",
      "CDSResults" : "2945073143148142603.json",
      "AlignedBodySWC" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/SWC/1734696429.swc",
      "PPPMResults" : "2941779068174991906.json"
    },
    "type" : "EMImage"
  } ]
}
""")

def test_EMImageLookup():
    lookup = ImageLookup(**by_body)
    assert len(lookup.results) == 1
    img = lookup.results[0]
    assert isinstance(img, EMImage)
    assert img.id == "2945073143148142603"
    assert img.libraryName == "FlyEM_Hemibrain_v1.2.1"
    assert img.publishedName == "hemibrain:v1.2.1:1734696429"
    assert img.alignmentSpace == "JRC2018_Unisex_20x_HR"
    assert img.gender == Gender.female
    assert img.files.CDM == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.png"
    assert img.files.CDMThumbnail == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.jpg"
    assert img.files.AlignedBodySWC == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/SWC/1734696429.swc"
    assert img.files.AlignedBodyOBJ == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/OBJ/1734696429.obj"
    assert img.files.CDSResults == "2945073143148142603.json"
    assert img.files.PPPMResults == "2941779068174991906.json"

    assert img.neuronType == "ORN_DA1"
    assert img.neuronInstance == "ORN_DA1_L"

ppp_results = json.loads(
"""
{
  "inputImage" : {
    "libraryName" : "FlyEM_Hemibrain_v1.2.1",
    "alignmentSpace" : "JRC2018_Unisex_20x_HR",
    "anatomicalArea" : "Brain",
    "gender" : "f",
    "neuronType" : "ORN_DA1",
    "neuronInstance" : "ORN_DA1_L",
    "id" : "2945073143148142603",
    "publishedName" : "hemibrain:v1.2.1:1734696429",
    "files" : {
      "CDM" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.png",
      "AlignedBodySWC" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/SWC/1734696429.swc",
      "store" : "fl:open_data:brain",
      "AlignedBodyOBJ" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/OBJ/1734696429.obj",
      "CDSResults" : "2945073143148142603.json",
      "CDMThumbnail" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.jpg",
      "PPPMResults" : "2941779068174991906.json"
    },
    "type" : "EMImage"
  },
  "results" : [ {
    "mirrored" : false,
    "image" : {
      "libraryName" : "FlyLight Gen1 MCFO",
      "alignmentSpace" : "JRC2018_Unisex_20x_HR",
      "anatomicalArea" : "Brain",
      "gender" : "m",
      "slideCode" : "20200124_63_B4",
      "objective" : "40x",
      "mountingProtocol" : "DPX PBS Mounting",
      "publishedName" : "VT023750",
      "files" : {
        "VisuallyLosslessStack" : "Gen1+MCFO/VT023750/VT023750-20200124_63_B4-m-40x-central-GAL4-JRC2018_Unisex_20x_HR-aligned_stack.h5j",
        "store" : "fl:open_data:brain"
      },
      "id" : "2765069201377853538",
      "type" : "LMImage"
    },
    "files" : {
      "SignalMip" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-raw.png",
      "store" : "fl:open_data:brain",
      "CDMBest" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-ch.png",
      "CDMBestThumbnail" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-ch.jpg",
      "SignalMipMaskedSkel" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-skel.png",
      "SignalMipMasked" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-masked_raw.png",
      "CDMSkel" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-ch_skel.png"
    },
    "pppmRank" : 0.0,
    "pppmScore" : 129,
    "type" : "PPPMatch"
  }
]}
"""
)

def test_PPPMatches():
    matches = PrecomputedMatches(**ppp_results)
    img = matches.inputImage
    assert isinstance(img, EMImage)
    assert img.id == "2945073143148142603"
    assert len(matches.results) == 1
    match = matches.results[0]
    assert isinstance(match, PPPMatch)
    assert isinstance(match.image, LMImage)
    assert match.image.id == "2765069201377853538"
    assert match.image.gender == Gender.male
    assert match.mirrored == False
    assert match.files.CDMBest == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/17/1734696429/1734696429-VT023750-20200124_63_B4-40x-JRC2018_Unisex_20x_HR-ch.png"


config = json.loads(
"""
{
    "anatomicalAreas": {
        "Brain": { 
            "label": "Brain",
            "alignmentSpace": "JRC2018_Unisex_20x_HR"
        },
        "VNC": { 
            "label": "Ventral Nerve Cord",
            "alignmentSpace": "JRC2018_VNC_Unisex_40x_DS"
        }
    },
    "stores": {
        "fl:open_data:brain": {
            "label": "FlyLight Brain Open Data Store",
            "anatomicalArea": "Brain",
            "prefixes": {
                "CDM": "https://s3.amazonaws.com/janelia-flylight-color-depth/",
                "CDMThumbnail": "https://s3.amazonaws.com/janelia-flylight-color-depth-thumbnails/",
                "CDMInput": "https://s3.amazonaws.com/janelia-flylight-color-depth/",
                "CDMMatch": "https://s3.amazonaws.com/janelia-flylight-color-depth/",
                "CDMBest": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "CDMBestThumbnail": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "CDMSkel": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "SignalMip": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "SignalMipMasked": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "SignalMipMaskedSkel": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "SignalMipExpression": "https://s3.amazonaws.com/janelia-ppp-match-prod/",
                "AlignedBodySWC": "https://s3.amazonaws.com/janelia-flylight-color-depth/",
                "AlignedBodyOBJ": "https://s3.amazonaws.com/janelia-flylight-color-depth/",
                "CDSResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-devpre/v3.0.0/metadata/cdsresults/",
                "PPPMResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-devpre/v3.0.0/metadata/pppresults/",
                "VisuallyLosslessStack": "https://s3.amazonaws.com/janelia-flylight-imagery/",
                "Gal4Expression": "https://s3.amazonaws.com/janelia-flylight-imagery/"
            },
            "customSearch": {
                "searchFolder": "searchable_neurons",
                "lmLibraries": [
                    {
                        "name": "FlyLight_Split-GAL4_Drivers",
                        "count": 68767
                    },
                    {
                        "name": "FlyLight_Gen1_MCFO",
                        "count": 349364
                    },
                    {
                        "name": "FlyLight_Annotator_Gen1_MCFO",
                        "count": 355179
                    }
                ],
                "emLibraries": [
                    {
                        "name": "FlyEM_Hemibrain_v1.2.1",
                        "publishedNamePrefix": "hemibrain:v1.2.1",
                        "count": 44477
                    }
                ]
            }
        }
    }
}
"""
)

def test_DataConfig():
    data_config = DataConfig(**config)

    assert data_config.anatomicalAreas["Brain"].alignmentSpace=="JRC2018_Unisex_20x_HR"
    assert data_config.anatomicalAreas["VNC"].alignmentSpace=="JRC2018_VNC_Unisex_40x_DS"
    
    alignmentSpaces = [data_config.anatomicalAreas[k].alignmentSpace for k in data_config.anatomicalAreas]

    for dataSetName in data_config.stores:
        store = data_config.stores[dataSetName]
        assert store.anatomicalArea in data_config.anatomicalAreas
