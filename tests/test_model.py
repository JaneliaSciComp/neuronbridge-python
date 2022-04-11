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

