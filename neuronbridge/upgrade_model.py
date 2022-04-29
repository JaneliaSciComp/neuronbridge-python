#!/usr/bin/env python
import os
import sys
import argparse
import enum
import json
from devtools import debug
import neuronbridge.legacy_model as legacy_model
import neuronbridge.model as model

data_version = "2.4.0"
data_version_vnc = "2.3.0-pre"

by_body_dir = f"/nrs/neuronbridge/v{data_version}/brain/mips/em_bodies"
by_line_dir = f"/nrs/neuronbridge/v{data_version}/brain/mips/all_mcfo_lines"
by_body_dir_vnc = f"/nrs/neuronbridge/v{data_version_vnc}/vnc/mips/em_bodies"
by_line_dir_vnc = f"/nrs/neuronbridge/v{data_version_vnc}/vnc/mips/gen1_mcfo_lines"

new_version = "3.0.0"

match_dirs = [
    f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flyem-vs-flylight",
    f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flylight-vs-flyem",
    f"/nrs/neuronbridge/v{data_version}/brain/pppresults/flyem-to-flylight.public"
]


VNC_ALIGNMENT_SPACE = "JRC2018_VNC_Unisex_40x_DS"
BRAIN_ALIGNMENT_SPACE = "JRC2018_Unisex_20x_HR"

img = '$img/'
thm = '$thm/'
ppp = '$ppp/'
swc = '$swc/'


#with open("test_data_v3/config.json") as f:
#    obj = model.DataConfig(**json.load(f))
#    debug(obj)

def write_json(obj, file=sys.stdout):
    json.dump(obj.dict(exclude_unset=True), file, indent=2)


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


def upgrade_lookup(lookup):
    if isinstance(lookup, legacy_model.LMImageLookup):
        return upgrade_lm_lookup(lookup)
    else:
        return upgrade_em_lookup(lookup)


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


def upgrade_matches(matches):
    if isinstance(matches, legacy_model.PPPMatches):
        return upgrade_ppp_matches(matches)
    else:
        return upgrade_cds_matches(matches)


def to_new(path):
    return path.replace(data_version, new_version).replace(data_version_vnc, new_version)


def convert(path, convert_lambda):
    with open(path) as f:
        obj = convert_lambda(json.load(f))
    newpath = to_new(path)
    if path == newpath:
        raise Exception("Cannot write back to same path: "+path)
    if new_version not in newpath:
        raise Exception("New path must contain new version: "+newpath)
    os.makedirs(os.path.dirname(newpath), exist_ok=True)
    with open(newpath, "w") as w:
        write_json(obj, w)
        print(f"Wrote {newpath}")
    return newpath


def convert_all(path, convert_lambda):
    for root, dirs, files in os.walk(path):
        for filename in files:
            try:
                filepath = f"{root}/{filename}"
                newpath = convert(filepath, convert_lambda)
            except Exception as err:
                print(f"Error converting {filepath}\n", err)
                raise err


def load_images(prefix, image_dirs, image_dict):
    """ Load image metadata into the given dict
    """
    for image_dir in image_dirs:
        for root, dirs, files in os.walk(image_dir):
            print(f"Loading image metadata from {root}")
            for filename in files:
                filepath = root+"/"+filename
                with open(filepath) as f:
                    try:
                        obj = json.load(f)
                        lookup = model.to_lookup(obj)
                        for image in lookup.results:
                            if isinstance(image, model.LMImage):
                                key = f"{prefix}~{image.slideCode}~{image.objective}~{image.channel}"
                            else:
                                key = f"{prefix}~{image.publishedName}"
                            images[key] = image
                    except Exception as err:
                        print(f"Error reading {filepath}\n", err)


def load_images_db(prefix, image_dirs):
    """ Load image metadata into the given dict
    """
    from pymongo import MongoClient
    client = MongoClient("mongodb://dev-mongodb/jacs")
    db = client.jacs
    col = db["temp_img"]

    for image_dir in image_dirs:
        for root, dirs, files in os.walk(image_dir):
            print(f"Loading image metadata from {root}")
            for filename in files:
                filepath = root+"/"+filename
                with open(filepath) as f:
                    try:
                        obj = json.load(f)
                        lookup = model.to_lookup(obj)
                        for image in lookup.results:
                            if isinstance(image, model.LMImage):
                                key = f"{prefix}~{image.slideCode}~{image.objective}~{image.channel}"
                            else:
                                key = f"{prefix}~{image.publishedName}"
                            new_obj = image.dict(exclude_unset=True)
                            new_obj['key'] = key
                            x = col.insert_one(new_obj)
                    except Exception as err:
                        print(f"Error reading {filepath}\n", err)

    #col.createIndex({"key":1},{"unique":True})


def convert_image(filepath):
    """ Convert the image metadata on the given path
    """
    with open(filepath) as f:
        obj = json.load(f)
        if 'slideCode' in obj:
            cons = legacy_model.LMImageLookup
        else:
            cons = legacy_model.EMImageLookup
        convert(filepath, lambda x: upgrade_lookup(cons(**x)))


def convert_match(filepath):
    """ Convert the match metadata on the given path
    """
    #convert("flylight-flyem-vnc.json", lambda x: upgrade_cds_matches(legacy_model.CDSMatches(**x)))
    #convert("pppresult.json", lambda x: upgrade_ppp_matches(legacy_model.PPPMatches(**x)))
    with open(filepath) as f:
        obj = json.load(f)
        if 'pppRank' in obj['results'][0]:
            cons = legacy_model.PPPMatches
        else:
            cons = legacy_model.CDSMatches
        convert(filepath, lambda x: upgrade_matches(legacy_model.CDSMatches(**x)))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert between data versions')
    parser.add_argument('-i', '--image', dest='input_image_path', type=str, required=False, \
            help='Path to a imageh file for conversion')
    parser.add_argument('-m', '--match', dest='input_match_path', type=str, required=False, \
            help='Path to a match file for conversion')
    parser.add_argument('--allimages', dest='allimages', action='store_true', \
        help='If --allimages, all of the images will be processed in serial')
    parser.add_argument('--allimagestodb', dest='allimagestodb', action='store_true', \
        help='If --allimages, all of the images will be loaded into MongoDB')
    parser.set_defaults(allimages=False)
    args = parser.parse_args()

    if args.allimages:
        convert_all(by_body_dir, lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))
        convert_all(by_line_dir, lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))
        convert_all(by_body_dir_vnc, lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))
        convert_all(by_line_dir_vnc, lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))

    if args.allimagestodb:
        load_images_db("brain", [to_new(p) for p in (by_body_dir,by_line_dir)])
        load_images_db("vnc", [to_new(p) for p in (by_body_dir_vnc,by_line_dir_vnc)])

    elif args.input_image_path:
        convert_image(args.input_image_path)

    elif args.input_match_path:
        #print("Loading image metadata into memory...")
        #image_dict = {}
        #load_images("brain", [to_new(p) for p in (by_body_dir,by_line_dir)], image_dict)
        #load_images("vnc", [to_new(p) for p in (by_body_dir_vnc,by_line_dir_vnc)], image_dict)
        #print("Loaded", len(images.keys()), "images")
        convert_match(args.input_match_path)

    else:
        parser.print_help(sys.stderr)

