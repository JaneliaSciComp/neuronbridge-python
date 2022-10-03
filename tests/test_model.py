import json

from neuronbridge.model import *
from neuronbridge.model import PPPMatch
from neuronbridge.model import LMImage

by_body = json.loads(
"""
{
  "results": [
    {
      "id": "2945073143148142603",
      "type": "EMImage",
      "libraryName": "FlyEM_Hemibrain_v1.2.1",
      "publishedName": "1734696429",
      "alignmentSpace": "JRC2018_Unisex_20x_HR",
      "anatomicalArea": "Brain",
      "gender": "f",
      "store": "fl:hemibrain:v1.2.1",
      "files": {
        "CDM": "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.png",
        "CDMThumbnail": "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.jpg",
        "AlignedBodySWC": "FlyEM_Hemibrain_v1.2.1/1734696429.swc",
        "AlignedBodyOBJ": "FlyEM_Hemibrain_v1.2.1/1734696429.obj",
        "CDSResults": "2945073143148142603.json",
        "PPPMResults": "1734696429.json"
      },
      "neuronType": "ORN_DA1",
      "neuronInstance": "ORN_DA1_L"
    }
  ]
}
""")

def test_EMImageLookup():
    lookup = ImageLookup(**by_body)
    assert len(lookup.results) == 1
    img = lookup.results[0]
    assert isinstance(img, EMImage)
    assert img.id == "2945073143148142603"
    assert img.libraryName == "FlyEM_Hemibrain_v1.2.1"
    assert img.publishedName == "1734696429"
    assert img.alignmentSpace == "JRC2018_Unisex_20x_HR"
    assert img.gender == Gender.female
    assert img.files.CDM == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.png"
    assert img.files.CDMThumbnail == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1734696429-JRC2018_Unisex_20x_HR-CDM.jpg"
    assert img.files.AlignedBodySWC == "FlyEM_Hemibrain_v1.2.1/1734696429.swc"
    assert img.files.AlignedBodyOBJ == "FlyEM_Hemibrain_v1.2.1/1734696429.obj"
    assert img.files.CDSResults == "2945073143148142603.json"
    assert img.files.PPPMResults == "1734696429.json"

    assert img.neuronType == "ORN_DA1"
    assert img.neuronInstance == "ORN_DA1_L"

ppp_results = json.loads(
"""
{
  "inputImage": {
    "id": "2945073144457764875",
    "type": "EMImage",
    "libraryName": "FlyEM_Hemibrain_v1.2.1",
    "publishedName": "2384750665",
    "anatomicalArea": "Brain",
    "alignmentSpace": "JRC2018_Unisex_20x_HR",
    "gender": "f",
    "store": "fl:hemibrain:v1.2.1",
    "files": {
      "CDM": "$img/JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/2384750665-JRC2018_Unisex_20x_HR-CDM.png",
      "CDMThumbnail": "$thm/JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/2384750665-JRC2018_Unisex_20x_HR-CDM.jpg",
      "AlignedBodySWC": "$swc/FlyEM_Hemibrain_v1.2.1/2384750665.swc"
    },
    "neuronType": null,
    "neuronInstance": null
  },
  "results": [
    {
      "type": "PPPMatch",
      "image": {
        "id": "2588090337243168866",
        "type": "LMImage",
        "libraryName": "FlyLight_Gen1_MCFO",
        "publishedName": "R20H11",
        "alignmentSpace": "JRC2018_Unisex_20x_HR",
        "gender": "f",
        "store": "fl:hemibrain:v1.2.1",
        "files": {
          "VisuallyLosslessStack": "https://s3.amazonaws.com/janelia-flylight-imagery/Gen1+MCFO/R20H11/R20H11-20180918_62_A5-f-40x-central-GAL4-JRC2018_Unisex_20x_HR-aligned_stack.h5j"
        },
        "slideCode": "20180918_62_A5",
        "objective": "40x",
        "anatomicalArea": "Brain",
        "mountingProtocol": "DPX PBS Mounting"
      },
      "files": {
        "CDM": "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-ch.png",
        "CDMSkel": "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-ch_skel.png",
        "SignalMip": "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-raw.png",
        "SignalMipMasked": "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-masked_raw.png",
        "SignalMipMaskedSkel": "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-skel.png"
      },
      "mirrored": true,
      "pppRank": 0.0,
      "pppScore": 144
    }
]}
"""
)

def test_PPPMatches():
    matches = PrecomputedMatches(**ppp_results)
    img = matches.inputImage
    assert isinstance(img, EMImage)
    assert img.id == "2945073144457764875"
    assert len(matches.results) == 1
    match = matches.results[0]
    assert isinstance(match, PPPMatch)
    assert isinstance(match.image, LMImage)
    assert match.image.id == "2588090337243168866"
    assert match.image.gender == Gender.female
    assert match.mirrored == True
    assert match.files.CDM == "23/2384750665/2384750665-R20H11-20180918_62_A5-40x-JRC2018_Unisex_20x_HR-ch.png"

new_results = json.loads(
"""{
  "inputImage" : {
    "id" : "2945073147357655051",
    "type": "EMImage",
    "libraryName" : "FlyEM_Hemibrain_v1.2.1",
    "publishedName" : "1253394541",
    "alignmentSpace" : "JRC2018_Unisex_20x_HR",
    "anatomicalArea": "Brain",
    "gender": "f",
    "neuronType" : "MC62",
    "neuronInstance" : "MC62(LWF5)_R",
    "store": "fl:hemibrain:v1.2.1",
    "files" : {
      "CDMThumbnail" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1253394541-JRC2018_Unisex_20x_HR-CDM.jpg",
      "CDM" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1253394541-JRC2018_Unisex_20x_HR-CDM.png",
      "AlignedBodySWC" : "FlyEM_Hemibrain_v1.2.1/1253394541.swc"
    }
  },
  "results" : [ {
    "type": "CDSMatch",
    "mirrored" : false,
    "normalizedScore" : 34433.96,
    "matchingPixels" : 73,
    "image" : {
      "id" : "2775341446398476299",
      "type": "LMImage",
      "libraryName" : "FlyLight Gen1 MCFO",
      "publishedName" : "VT040712",
      "alignmentSpace" : "JRC2018_Unisex_20x_HR",
      "anatomicalArea" : "Brain",
      "gender" : "m",
      "slideCode" : "20200221_64_H4",
      "objective" : "40x",
      "mountingProtocol" : "DPX PBS Mounting",
      "channel" : 2,
      "store": "fl:hemibrain:v1.2.1",
      "files" : {
        "CDMThumbnail" : "JRC2018_Unisex_20x_HR/FlyLight_Gen1_MCFO/VT040712-20200221_64_H4-GAL4-m-40x-brain-JRC2018_Unisex_20x_HR-CDM_2.jpg",
        "CDM" : "JRC2018_Unisex_20x_HR/FlyLight_Gen1_MCFO/VT040712-20200221_64_H4-GAL4-m-40x-brain-JRC2018_Unisex_20x_HR-CDM_2.png",
        "VisuallyLosslessStack" : "Gen1+MCFO/VT040712/VT040712-20200221_64_H4-m-40x-central-GAL4-JRC2018_Unisex_20x_HR-aligned_stack.h5j",
        "Gal4Expression" : "Gen1/CDM/VT040712/VT040712-sample_003501-f-20x-brain-JRC2018_Unisex_20x_HR-CDM_1.png"
      }
    },
    "files" : {
      "CDMMatch" : "VT040712-20200221_64_H4-GAL4-m-40x-brain-JRC2018_Unisex_20x_HR-CDM_2-04.png",
      "CDMInput" : "1253394541-JRC2018_Unisex_20x_HR-CDM.png"
    }
  }]
}
"""
)

def test_NewMatches():
    matches = PrecomputedMatches(**new_results)
    assert isinstance(matches.inputImage, EMImage)
    match = matches.results[0]
    assert isinstance(match, CDSMatch)
    assert isinstance(match.image, LMImage)


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
        "fl:hemibrain:v1.2.1": {
            "label": "FlyLight vs Hemibrain",
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
                "AlignedBodySWC": "https://s3.amazonaws.com/janelia-flylight-color-depth/SWC/",
                "AlignedBodyOBJ": "https://s3.amazonaws.com/janelia-flylight-color-depth/OBJ/",
                "CDSResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-prod/v3.0.0-alpha/metadata/cdsresults/",
                "PPPMResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-prod/v3.0.0-alpha/metadata/pppresults/",
                "VisuallyLosslessStack": "https://s3.amazonaws.com/janelia-flylight-imagery/"
            },
            "customSearch": {
                "alignmentSpace": "JRC2018_Unisex_20x_HR",
                "searchFolder": "searchable_neurons",
                "lmLibraries": [
                    "FlyLight_Split-GAL4_Drivers",
                    "FlyLight_Gen1_MCFO",
                    "FlyLight_Annotator_Gen1_MCFO"
                ],
                "emLibraries": [
                    "FlyEM_Hemibrain_v1.2.1"
                ]
            }
        },
        "fl:vnc:latest": {
            "label": "FlyLight vs VNC",
            "anatomicalArea": "VNC",
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
                "AlignedBodySWC": "https://s3.amazonaws.com/janelia-flylight-color-depth/SWC/",
                "AlignedBodyOBJ": "https://s3.amazonaws.com/janelia-flylight-color-depth/OBJ/",
                "CDSResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-prod/v3.0.0-alpha/metadata/cdsresults/",
                "PPPMResults": "https://s3.amazonaws.com/janelia-neuronbridge-data-prod/v3.0.0-alpha/metadata/pppresults/",
                "VisuallyLosslessStack": "https://s3.amazonaws.com/janelia-flylight-imagery/"
            },
            "customSearch": {
                "alignmentSpace": "JRC2018_VNC_Unisex_40x_DS",
                "searchFolder": "searchable_neurons",
                "lmLibraries": [
                    "FlyLight_Split-GAL4_Drivers",
                    "FlyLight_Gen1_MCFO"
                ],
                "emLibraries": [
                    "FlyEM_VNC_v0.6"
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
        assert store.customSearch.alignmentSpace in alignmentSpaces
