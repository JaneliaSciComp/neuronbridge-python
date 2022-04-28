#!/usr/bin/env python
import enum
import json
from devtools import debug
import neuronbridge.legacy_model as legacy_model
import neuronbridge.model as model

VNC_ALIGNMENT_SPACE = "JRC2018_VNC_Unisex_40x_DS"
BRAIN_ALIGNMENT_SPACE = "JRC2018_Unisex_20x_HR"

img = '$img/'
thm = '$thm/'
ppp = '$ppp/'
swc = '$swc/'


with open("test_data_v3/config.json") as f:
    obj = model.DataConfig(**json.load(f))
    #debug(obj)


def upgrade_em_lookup(em_lookup : legacy_model.EMImageLookup):
    return model.EMImageLookup(results = [ 
        model.EMImage(
            id = old_image.id,
            libraryName = old_image.libraryName,
            publishedName = old_image.publishedName,
            gender = old_image.gender,
            alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in old_image.imageURL else BRAIN_ALIGNMENT_SPACE,
            neuronType = old_image.neuronType,
            neuronInstance = old_image.neuronInstance,
            files = model.Files(
                ColorDepthMip = img + old_image.imageURL,
                ColorDepthMipThumbnail = thm + old_image.thumbnailURL
            )
        )
        for old_image in em_lookup.results 
    ])


def upgrade_lm_lookup(lm_lookup : legacy_model.LMImageLookup):
    return model.LMImageLookup(results=[
        model.LMImage(
            id = old_image.id,
            libraryName = old_image.libraryName,
            publishedName = old_image.publishedName,
            gender = old_image.gender,
            alignmentSpace = old_image.alignmentSpace,
            slideCode = old_image.slideCode,
            objective = old_image.objective,
            mountingProtocol = old_image.mountingProtocol,
            anatomicalArea = old_image.anatomicalArea,
            channel = old_image.channel,
            files = model.Files(
                ColorDepthMip = img + old_image.imageURL,
                ColorDepthMipThumbnail = thm + old_image.thumbnailURL
            )
        )
        for old_image in lm_lookup.results
    ])


def upgrade_cds_match(old_match):

    if old_match.libraryName.startswith("FlyEM"):
        image = model.EMImage(
            id = old_match.id,
            libraryName = old_match.libraryName,
            publishedName = old_match.publishedName,
            gender = old_match.gender,
            alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in old_match.imageURL else BRAIN_ALIGNMENT_SPACE,
            neuronType = old_match.neuronType,
            neuronInstance = old_match.neuronInstance,
            files = model.Files(
                ColorDepthMip = img+old_match.imageURL,
                ColorDepthMipThumbnail = thm + old_match.thumbnailURL,
                ColorDepthMipMatched = img + old_match.alignmentSpace+"/"+old_match.libraryName+"/"+old_match.searchablePNG,
                AlignedBodySWC = swc + old_match.libraryName + "/" + old_match.publishedName + ".swc",
            )
        )
    else:
        image = model.LMImage(
            id = old_match.id,
            libraryName = old_match.libraryName,
            publishedName = old_match.publishedName,
            gender = old_match.gender,
            alignmentSpace = old_match.alignmentSpace,
            slideCode = old_match.slideCode,
            objective = old_match.objective,
            mountingProtocol = old_match.mountingProtocol,
            anatomicalArea = old_match.anatomicalArea,
            channel = old_match.channel,
            files = model.Files(
                ColorDepthMip = img + old_match.imageURL,
                ColorDepthMipThumbnail = thm + old_match.thumbnailURL,
                ColorDepthMipMatched = img + old_match.alignmentSpace+"/"+old_match.libraryName+"/searchable_neurons/pngs/"+old_match.searchablePNG,
                VisuallyLosslessStack = old_match.imageStack,
            )
        )
    return model.CDSMatch(
            image = image,
            mirrored = old_match.mirrored,
            normalizedScore = old_match.normalizedScore,
            matchingPixels = old_match.matchingPixels,
        )


def upgrade_cds_matches(cds_matches : legacy_model.CDSMatches):

    if cds_matches.maskLibraryName.startswith("FlyEM"):
        inputImage = model.EMImage(
            id = cds_matches.maskId,
            libraryName = cds_matches.maskLibraryName,
            publishedName = cds_matches.maskPublishedName,
            gender = "f" if "VNC" in cds_matches.maskLibraryName else "m",
            # TODO: look these up
            alignmentSpace = "",
            neuronType = "",
            neuronInstance = "",
            files = model.Files(
                AlignedBodySWC = swc + cds_matches.maskLibraryName + "/" + cds_matches.maskPublishedName + ".swc",
            )
        )
    else:
        inputImage = model.LMImage(
            id = cds_matches.maskId,
            libraryName = cds_matches.maskLibraryName,
            publishedName = cds_matches.maskPublishedName,
            # TODO: look these up
            gender = model.Gender.female,
            alignmentSpace = "",
            slideCode = "",
            objective = "",
            mountingProtocol = "",
            anatomicalArea = "",
            channel = 0,
            files = model.Files(
                VisuallyLosslessStack = cds_matches.maskImageStack,
            )
        )

    return model.Matches(
        inputImage=inputImage,
        results=[
            upgrade_cds_match(old_match)
            for old_match in cds_matches.results
        ]
    )


def upgrade_ppp_match(old_match):

    image = model.LMImage(
        id = old_match.id,
        libraryName = old_match.libraryName,
        publishedName = old_match.publishedName,
        gender = old_match.gender,
        alignmentSpace = old_match.alignmentSpace,
        slideCode = old_match.slideCode,
        objective = old_match.objective,
        mountingProtocol = old_match.mountingProtocol,
        anatomicalArea = "VNC" if "VNC" in old_match.alignmentSpace else "Brain",
        files = model.Files(
            ColorDepthMip = ppp + old_match.files.ColorDepthMip,
            ColorDepthMipSkel = ppp + old_match.files.ColorDepthMipSkel,
            SignalMip = ppp + old_match.files.SignalMip,
            SignalMipMasked = ppp + old_match.files.SignalMipMasked,
            SignalMipMaskedSkel = ppp + old_match.files.SignalMipMaskedSkel,
            VisuallyLosslessStack = old_match.imageStack,
        )
    )
    return model.PPPMatch(
            image = image,
            mirrored = old_match.mirrored,
            pppRank = old_match.pppRank,
            pppScore = old_match.pppScore,
        )


def upgrade_ppp_matches(ppp_matches : legacy_model.PPPMatches):

    inputImage = model.EMImage(
        id = ppp_matches.maskId,
        libraryName = ppp_matches.maskLibraryName,
        publishedName = ppp_matches.maskPublishedName,
        gender = "f" if "VNC" in ppp_matches.maskLibraryName else "m",
        alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in ppp_matches.maskLibraryName else BRAIN_ALIGNMENT_SPACE,
        neuronType = ppp_matches.neuronType,
        neuronInstance = ppp_matches.neuronInstance,
        files = model.Files(
            # TODO: look these up
            AlignedBodySWC = swc + ppp_matches.maskLibraryName + "/" + ppp_matches.maskPublishedName + ".swc",
        )
    )

    return model.Matches(
        inputImage=inputImage,
        results=[
            upgrade_ppp_match(old_match)
            for old_match in ppp_matches.results
        ]
    )

if __name__ == '__main__':

    pass
