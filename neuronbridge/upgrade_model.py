#!/usr/bin/env python
import os
import sys
import argparse
import traceback
import rapidjson
from pymongo import MongoClient
import neuronbridge.legacy_model as legacy_model
import neuronbridge.model as model

DEBUG = False
data_version = "2.4.0"
data_version_vnc = "2.3.0-pre"

by_body_dir = [
    f"/nrs/neuronbridge/v{data_version}/brain/mips/em_bodies"
]
by_line_dir = [
    f"/nrs/neuronbridge/v{data_version}/brain/mips/all_mcfo_lines",
    f"/nrs/neuronbridge/v{data_version}/brain/mips/split_gal4_lines",
]
by_body_dir_vnc = [
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/mips/em_bodies"
]
by_line_dir_vnc = [
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/mips/gen1_mcfo_lines",
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/mips/split_gal4_lines_published",
]
match_dirs = [
    f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flyem-vs-flylight",
    f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flylight-vs-flyem",
    f"/nrs/neuronbridge/v{data_version}/brain/pppresults/flyem-to-flylight.public",
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/cdsresults.final/flyem-vs-flylight",
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/cdsresults.final/flylight-vs-flyem",
    f"/nrs/neuronbridge/v{data_version_vnc}/vnc/pppresults/flyem-to-flylight.public"
]

new_version = "3.0.0-alpha"

BRAIN_ANATOMICAL_AREA = "Brain"
BRAIN_ALIGNMENT_SPACE = "JRC2018_Unisex_20x_HR"
VNC_ANATOMICAL_AREA = "VNC"
VNC_ALIGNMENT_SPACE = "JRC2018_VNC_Unisex_40x_DS"
HEMIBRAIN_LIBRARY = "FlyEM_Hemibrain_v1.2.1"

client = MongoClient("mongodb://dev-mongodb/jacs")

def write_json(obj, file=sys.stdout):
    rapidjson.dump(obj.dict(exclude_none=True), file, indent=2)


def get_mongo_img():
    return client.jacs["temp_img"]


def get_mongo_nb():
    return client.jacs["publishedImage"]


def get_matched(alignmentSpace, libraryName, searchable):
    if not searchable: return None
    return alignmentSpace +"/"+ libraryName.replace(" ","_") + "/searchable_neurons/pngs/" + searchable


def get_pppm_path(old_match, file_path):
    if not file_path: return None
    return old_match.alignmentSpace + "/" + HEMIBRAIN_LIBRARY + "/" + file_path


def upgrade_em_lookup(em_lookup : legacy_model.EMImageLookup):
    return model.ImageLookup(results = [
        model.EMImage(
            id = old_image.id,
            libraryName = old_image.libraryName,
            publishedName = old_image.publishedName,
            gender = old_image.gender,
            anatomicalArea = VNC_ANATOMICAL_AREA if "VNC" in old_image.imageURL else BRAIN_ANATOMICAL_AREA,
            alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in old_image.imageURL else BRAIN_ALIGNMENT_SPACE,
            neuronType = old_image.neuronType,
            neuronInstance = old_image.neuronInstance,
            files = model.Files(
                store = "prod",
                CDM = old_image.imageURL,
                CDMThumbnail = old_image.thumbnailURL,
                AlignedBodySWC = old_image.libraryName + "/" + old_image.publishedName + ".swc",
                AlignedBodyOBJ = old_image.libraryName + "/" + old_image.publishedName + ".obj",
                CDSResults = old_image.id+".json",
                PPPMResults = old_image.publishedName+".json"
            )
        )
        for old_image in em_lookup.results
    ])


def get_h5j(old_image):
    col = get_mongo_nb()
    res = list(col.find({
            "slideCode":old_image.slideCode,
            "objective":old_image.objective,
            "alignmentSpace":old_image.alignmentSpace,
    }))
    if res:
        return res[0]["files"]["VisuallyLosslessStack"]
    else:
        print(f"Error: no h5j found for {old_image.slideCode} {old_image.objective} {old_image.alignmentSpace}", file=sys.stderr)
        return None


def upgrade_lm_lookup(lm_lookup : legacy_model.LMImageLookup):
    return model.ImageLookup(results=[
        model.LMImage(
            id = old_image.id,
            libraryName = old_image.libraryName,
            publishedName = old_image.publishedName,
            gender = old_image.gender,
            anatomicalArea = old_image.anatomicalArea,
            alignmentSpace = old_image.alignmentSpace,
            slideCode = old_image.slideCode,
            objective = old_image.objective,
            mountingProtocol = old_image.mountingProtocol,
            channel = old_image.channel,
            files = model.Files(
                store = "prod",
                CDM = old_image.imageURL,
                CDMThumbnail = old_image.thumbnailURL,
                VisuallyLosslessStack = get_h5j(old_image),
                CDSResults = old_image.id+".json"
            )
        )
        for old_image in lm_lookup.results
    ])


def upgrade_lookup(lookup):
    if isinstance(lookup, legacy_model.LMImageLookup):
        return upgrade_lm_lookup(lookup)
    else:
        return upgrade_em_lookup(lookup)


def upgrade_cds_match(input_image, old_match):
    if old_match.libraryName.startswith("FlyEM"):
        image = model.EMImage(
            id = old_match.id,
            libraryName = old_match.libraryName,
            publishedName = old_match.publishedName,
            gender = old_match.gender,
            anatomicalArea = VNC_ANATOMICAL_AREA if "VNC" in old_match.imageURL else BRAIN_ANATOMICAL_AREA,
            alignmentSpace = VNC_ALIGNMENT_SPACE if "VNC" in old_match.imageURL else BRAIN_ALIGNMENT_SPACE,
            neuronType = old_match.neuronType,
            neuronInstance = old_match.neuronInstance,
            files = model.Files(
                store = "prod",
                CDM = old_match.imageURL,
                CDMThumbnail = old_match.thumbnailURL,
                AlignedBodySWC = old_match.libraryName + "/" + old_match.publishedName + ".swc",
                AlignedBodyOBJ = old_match.libraryName + "/" + old_match.publishedName + ".obj",
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
                store = "prod",
                CDM = old_match.imageURL,
                CDMThumbnail = old_match.thumbnailURL,
                VisuallyLosslessStack = old_match.imageStack,
            )
        )
    return model.CDSMatch(
            image = image,
            mirrored = old_match.mirrored,
            normalizedScore = old_match.normalizedScore,
            matchingPixels = old_match.matchingPixels,
            files = model.Files(
                store = "prod",
                CDMInput = get_matched(input_image.alignmentSpace, input_image.libraryName, old_match.sourceSearchablePNG),
                CDMMatch = get_matched(old_match.alignmentSpace, old_match.libraryName, old_match.searchablePNG),
            )
        )


def upgrade_cds_matches(cds_matches : legacy_model.CDSMatches):
    col = get_mongo_img()
    res = list(col.find({"id":cds_matches.maskId}))
    if res:
        moimg = res[0]
    else:
        print("Error: no image found for CDS target "+cds_matches.maskId, file=sys.stderr)
        return None

    # extra fields are forbidden by the model, so we need to delete the Mongo id
    del moimg['_id']

    if moimg['type'] == "LMImage":
        image = model.LMImage(**moimg)
    else:
        image = model.EMImage(**moimg)
    return model.PrecomputedMatches(
        inputImage=image,
        results=[
            upgrade_cds_match(image, old_match)
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
            store = "prod",
            VisuallyLosslessStack = old_match.imageStack,
        )
    )
    return model.PPPMatch(
            image = image,
            mirrored = old_match.mirrored,
            pppRank = old_match.pppRank,
            pppScore = old_match.pppScore,
            files = model.Files(
                store = "prod",
                CDMBest = get_pppm_path(old_match, old_match.files.ColorDepthMip),
                CDMBestThumbnail = get_pppm_path(old_match, old_match.files.ColorDepthMip.replace(".png",".jpg")),
                CDMSkel = get_pppm_path(old_match, old_match.files.ColorDepthMipSkel),
                SignalMip = get_pppm_path(old_match, old_match.files.SignalMip),
                SignalMipMasked = get_pppm_path(old_match, old_match.files.SignalMipMasked),
                SignalMipMaskedSkel = get_pppm_path(old_match, old_match.files.SignalMipMaskedSkel),
            )
        )


def upgrade_ppp_matches(ppp_matches : legacy_model.PPPMatches):
    col = get_mongo_img()
    res = list(col.find({"publishedName":ppp_matches.maskPublishedName}))
    if res:
        moimg = res[0]
    else:
        print("Warning: no image found for PPPM target "+ppp_matches.maskPublishedName, file=sys.stderr)
        return None

    # extra fields are forbidden by the model, so we need to delete the Mongo id
    del moimg['_id']
    
    return model.PrecomputedMatches(
        inputImage=model.EMImage(**moimg),
        results=[
            upgrade_ppp_match(old_match)
            for old_match in ppp_matches.results
            if old_match.files
        ]
    )


def upgrade_matches(matches):
    if isinstance(matches, legacy_model.PPPMatches):
        m = upgrade_ppp_matches(matches)
    else:
        m = upgrade_cds_matches(matches)

    if not m: return None

    if m.results and isinstance(m.results[0], model.CDSMatch) and isinstance(m.inputImage, model.EMImage):
        results = []
        counts = dict()
        for result in m.results:
            desc = f"{result.image.publishedName} {result.image.slideCode} with {result.normalizedScore} and {result.matchingPixels}"
            if len(counts.keys()) < 300:
                c = counts.get(result.image.publishedName, 0)
                # TODO: use top 3 samples not images
                if c < 3:
                    if DEBUG: print(f"Keep result {desc}")
                    results.append(result)
                else:
                    if DEBUG: print(f"DROP result {desc}")
            else:
                if DEBUG: print(f"DROP result {desc} (over 300 lines)")
            counts[result.image.publishedName] = c + 1

        print(f"Truncating {len(m.results)} results to {len(results)}")
        m.results = results
    else:
        print(f"Keeping {len(m.results)} results")

    return m


def to_new(path):
    return path.replace(data_version, new_version).replace(data_version_vnc, new_version)


def convert(path, convert_lambda):
    with open(path) as f:
        obj = convert_lambda(rapidjson.load(f))
    if not obj:
        print("Could not convert", path)
        return None
    newpath = to_new(path)
    if path == newpath:
        raise Exception("Cannot write back to same path: "+path)
    if new_version not in newpath:
        raise Exception("New path must contain new version: "+newpath)
    os.makedirs(os.path.dirname(newpath), exist_ok=True)
    with open(newpath, "w") as w:
        write_json(obj, w)
        print("Wrote", newpath)
    return newpath


def convert_all(paths, convert_lambda):
    for path in paths:
        for root, dirs, files in os.walk(path):
            for filename in files:
                try:
                    filepath = f"{root}/{filename}"
                    newpath = convert(filepath, convert_lambda)
                except Exception as err:
                    print(f"Error converting {filepath}\n", err)
                    raise err


def load_images_db(prefix, image_dirs):
    """ Load image metadata into the given dict
    """
    col = get_mongo_img()
    for image_dir in image_dirs:
        for root, dirs, files in os.walk(image_dir):
            print(f"Loading image metadata from {root}")
            for filename in files:
                filepath = root+"/"+filename
                with open(filepath) as f:
                    try:
                        obj = rapidjson.load(f)
                        lookup = model.ImageLookup(**obj)
                        for image in lookup.results:
                            new_obj = image.dict(exclude_unset=True)
                            x = col.insert_one(new_obj)
                    except Exception as err:
                        print(f"Error reading {filepath}\n", err)


def convert_image(filepath):
    """ Convert the image metadata on the given path
    """
    with open(filepath) as f:
        obj = rapidjson.load(f)
        if 'slideCode' in obj['results'][0]:
            cons = legacy_model.LMImageLookup
        else:
            cons = legacy_model.EMImageLookup
        return convert(filepath, lambda x: upgrade_lookup(cons(**x)))


def convert_match(filepath):
    """ Convert the match metadata on the given path
    """
    with open(filepath) as f:
        obj = rapidjson.load(f)
        if obj['results'] and 'pppRank' in obj['results'][0]:
            cons = legacy_model.PPPMatches
        else:
            cons = legacy_model.CDSMatches
        return convert(filepath, lambda x: upgrade_matches(cons(**x)))



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert between data versions')
    parser.add_argument('-i', '--image', dest='input_image_path', type=str, required=False, \
            help='Path to an old image file for conversion')
    parser.add_argument('-m', '--match', dest='input_match_path', type=str, required=False, \
            help='Path to an old match file for conversion')
    parser.add_argument('--allimages', dest='allimages', action='store_true', \
        help='If --allimages, all of the old images will be processed in serial to create new images in the appropriate locations')
    parser.add_argument('--allimagestodb', dest='allimagestodb', action='store_true', \
        help='If --allimagestodb, all of the new images will be loaded into MongoDB')
    parser.add_argument('--filelists', dest='filelists', action='store_true', \
        help='If --filelists, then a list of files will be generates for each match dir, so that the matches can be processed in parallel on the cluster.')
    parser.add_argument('--validate', dest='validate', action='store_true', \
        help='If --validate, the new images and matches will be validated, and any issues logged.')
    parser.set_defaults(allimages=False)
    parser.set_defaults(allimagestodb=False)
    parser.set_defaults(filelists=False)
    parser.set_defaults(validate=False)
    args = parser.parse_args()

    if args.allimages:
        convert_all(by_line_dir, lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))
        convert_all(by_body_dir, lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))
        convert_all(by_line_dir_vnc, lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))
        convert_all(by_body_dir_vnc, lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))

    elif args.allimagestodb:
        print("Manually drop the table in the dev database: ")
        print("    db.temp_img.drop()")
        input("Press enter when ready...")
        load_images_db("brain", [to_new(p) for p in by_body_dir])
        load_images_db("brain", [to_new(p) for p in by_line_dir])
        load_images_db("vnc", [to_new(p) for p in by_body_dir_vnc])
        load_images_db("vnc", [to_new(p) for p in by_line_dir_vnc])
        print("Manually run these statements on the dev database: ")
        print("    db.temp_img.createIndex({id:1},{unique:true})")
        print("    db.temp_img.createIndex({publishedName:1})")

    elif args.input_image_path:
        convert_image(args.input_image_path)

    elif args.input_match_path:
        if args.input_match_path.endswith(".txt"):
            with open(args.input_match_path) as f:
                for line in f:
                    try:
                        convert_match(line.rstrip())
                    except Exception as err:
                        print("Error converting "+line, file=sys.stderr)
                        print(traceback.format_exc(), file=sys.stderr)
        else:
            convert_match(args.input_match_path)

    elif args.filelists:
        c = 1
        i = 0
        count = 0
        os.makedirs("filelists", exist_ok=True)
        writer = open(f"filelists/filelist_{c}.txt", "w")
        for match_dir in match_dirs:
            print("Walking", match_dir)
            for root, dirs, files in os.walk(match_dir):
                for filepath in files:
                    writer.write(f"{root}/{filepath}\n")
                    i += 1
                    if i >= 10000:
                        c += 1
                        writer.close()
                        writer = open(f"filelists/filelist_{c}.txt", "w")
                        i = 0
        writer.close()

    else:
        parser.print_help(sys.stderr)
