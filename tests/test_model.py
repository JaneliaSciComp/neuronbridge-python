import pytest
import json

from neuronbridge.model import *

by_body = json.loads(
"""
{
  "results" : [ {
    "id" : "2943465148721623051",
    "publishedName" : "1001453586",
    "libraryName" : "FlyEM_Hemibrain_v1.2.1",
    "imageURL" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1001453586-JRC2018_Unisex_20x_HR-CDM.png",
    "thumbnailURL" : "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1001453586-JRC2018_Unisex_20x_HR-CDM.jpg",
    "neuronType" : "KCa'b'-ap1",
    "neuronInstance" : "KCa'b'-ap1_R",
    "gender" : "f"
  } ]
}
""")

def test_EMImageLookup():
    lookup = EMImageLookup(**by_body)
    assert len(lookup.results) == 1
    img = lookup.results[0]
    assert img.id == "2943465148721623051"
    assert img.publishedName == "1001453586"
    assert img.libraryName == "FlyEM_Hemibrain_v1.2.1"
    assert img.imageURL == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1001453586-JRC2018_Unisex_20x_HR-CDM.png"
    assert img.thumbnailURL == "JRC2018_Unisex_20x_HR/FlyEM_Hemibrain_v1.2.1/1001453586-JRC2018_Unisex_20x_HR-CDM.jpg"
    assert img.neuronType == "KCa'b'-ap1"
    assert img.neuronInstance == "KCa'b'-ap1_R"
    assert img.gender == Gender.female

ppp_results = json.loads(
"""
{
  "maskId": "2941779053884998178",
  "maskPublishedName": "636798093",
  "maskLibraryName": "FlyEM_Hemibrain_v1.2.1",
  "neuronType": "LHPV5c1_a",
  "neuronInstance": "LHPV5c1_a_R",
  "results": [
    {
      "id": "2422546586627211362",
      "publishedName": "VT043138",
      "libraryName": "FlyLight_Gen1_MCFO",
      "pppRank": 0.0,
      "pppScore": 118,
      "slideCode": "20170616_61_E3",
      "objective": "40x",
      "gender": "m",
      "alignmentSpace": "JRC2018_Unisex_20x_HR",
      "mountingProtocol": "DPX PBS Mounting",
      "coverageScore": -118.74299431298442,
      "aggregateCoverage": 96.55475533690863,
      "mirrored": true,
      "files": {
        "ColorDepthMip": "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-ch.png",
        "SignalMipMaskedSkel": "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-skel.png",
        "ColorDepthMipSkel": "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-ch_skel.png",
        "SignalMip": "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-raw.png",
        "SignalMipMasked": "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-masked_raw.png"
      },
      "imageStack": "https://s3.amazonaws.com/janelia-flylight-imagery/Gen1+MCFO/VT043138/VT043138-20170616_61_E3-m-40x-central-GAL4-JRC2018_Unisex_20x_HR-aligned_stack.h5j"
    }
]}
"""
)

def test_PPPMatches():
    ppp = PPPMatches(**ppp_results)
    assert ppp.maskId == "2941779053884998178"
    assert len(ppp.results) == 1
    img = ppp.results[0]
    assert img.id == "2422546586627211362"
    assert img.mirrored == True
    assert img.gender == Gender.male
    assert img.files.ColorDepthMip == "63/636798093/636798093-VT043138-20170616_61_E3-40x-JRC2018_Unisex_20x_HR-ch.png"
