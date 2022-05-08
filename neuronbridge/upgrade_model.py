#!/usr/bin/env python
import os
import sys
import argparse
import traceback
import enum
import rapidjson
import itertools
from devtools import debug
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

new_version = "3.0.0"

VNC_ALIGNMENT_SPACE = "JRC2018_VNC_Unisex_40x_DS"
BRAIN_ALIGNMENT_SPACE = "JRC2018_Unisex_20x_HR"

img = '$img/'
thm = '$thm/'
ppp = '$ppp/'
swc = '$swc/'

client = MongoClient("mongodb://dev-mongodb/jacs")


error_counts = {}
def error(s, *tags):
    if s in error_counts:
        error_counts[s] += 1
    else:
        error_counts[s] = 1
    if error_counts[s] < 10:
        print(f"{s}:", *tags, file=sys.stderr)
    if error_counts[s] == 10:
        print(f"Reached maximum logging count for '{s}'", file=sys.stderr)


def write_json(obj, file=sys.stdout):
    rapidjson.dump(obj.dict(exclude_unset=True), file, indent=2)


def get_mongo_img():
    return client.jacs["temp_img"]


def get_mongo_nb():
    return client.jacs["publishedImage"]


def get_matched(alignmentSpace, libraryName, searchable):
    if not searchable: return None
    return img + alignmentSpace +"/"+ libraryName.replace(" ","_") + "/searchable_neurons/pngs/" + searchable


def upgrade_em_lookup(em_lookup : legacy_model.EMImageLookup):
    return model.ImageLookup(results = [
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
                ColorDepthMipThumbnail = thm + old_image.thumbnailURL,
                AlignedBodySWC = swc + old_image.libraryName + "/" + old_image.publishedName + ".swc",
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
            alignmentSpace = old_image.alignmentSpace,
            slideCode = old_image.slideCode,
            objective = old_image.objective,
            mountingProtocol = old_image.mountingProtocol,
            anatomicalArea = old_image.anatomicalArea,
            channel = old_image.channel,
            files = model.Files(
                ColorDepthMip = img + old_image.imageURL,
                ColorDepthMipThumbnail = thm + old_image.thumbnailURL,
                VisuallyLosslessStack = get_h5j(old_image)
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
                ColorDepthMipInput = get_matched(old_match.alignmentSpace, old_match.libraryName, old_match.sourceSearchablePNG),
                ColorDepthMipMatch = get_matched(old_match.alignmentSpace, old_match.libraryName, old_match.searchablePNG),
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
                ColorDepthMipInput = get_matched(old_match.alignmentSpace, old_match.libraryName, old_match.sourceSearchablePNG),
                ColorDepthMipMatch = get_matched(old_match.alignmentSpace, old_match.libraryName, old_match.searchablePNG),
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
    col = get_mongo_img()
    res = list(col.find({"id":cds_matches.maskId}))
    if res:
        moimg = res[0]
    else:
        print("Error: no image found for CDS target "+cds_matches.maskId, file=sys.stderr)
        return None

    if 'slideCode' in moimg:
        # TODO: this is only necessary because these do not appear in the image files
        image = model.LMImage(**moimg)
        image.files.VisuallyLosslessStack = cds_matches.maskImageStack
    else:
        image = model.EMImage(**moimg)
    return model.Matches(
        inputImage=image,
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
    col = get_mongo_img()
    res = list(col.find({"publishedName":ppp_matches.maskPublishedName}))
    if res:
        moimg = res[0]
    else:
        print("Warning: no image found for PPPM target "+ppp_matches.maskPublishedName, file=sys.stderr)
        return None

    return model.Matches(
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

    return m if m.results else None


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


def validate(image, filepath):
    if not image.files.ColorDepthMip:
        error("Missing ColorDepthMip", image.id, filepath)
    if not image.files.ColorDepthMipThumbnail:
        error("Missing ColorDepthMipThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            error("Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            error("Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            error("Missing AlignedBodySWC", image.id, filepath)


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

    elif args.validate:

        try:
            validateImageLookups = True
            validatePublishedNames = True

            publishedNames = set()
            if validateImageLookups:
                for image_dir in itertools.chain.from_iterable([by_line_dir, by_body_dir, by_line_dir_vnc, by_body_dir_vnc]):
                    for root, dirs, files in os.walk(to_new(image_dir)):
                        print(f"Validating images from {root}")
                        c = 0
                        for filename in files:
                            filepath = root+"/"+filename
                            err = lambda msg: error(f"{msg}: {filepath}")
                            with open(filepath) as f:
                                obj = rapidjson.load(f)
                                lookup = model.ImageLookup(**obj)
                                if not lookup.results:
                                    error(f"No images")
                                for image in lookup.results:
                                    validate(image, filepath)
                                    publishedNames.add(image.publishedName)
                                c += 1
                        print(f"    Checked {c} matches")

            print(f"Indexed {len(publishedNames)} published names")

            for match_dir in match_dirs:
                for root, dirs, files in os.walk(to_new(match_dir)):
                    print(f"Validating matches from {root}")
                    c = 0
                    for filename in files:
                        filepath = root+"/"+filename
                        with open(filepath) as f:
                            obj = rapidjson.load(f)
                            matches = model.Matches(**obj)
                            validate(matches.inputImage, filepath)
                            if validatePublishedNames and matches.inputImage.publishedName not in publishedNames:
                                error(f"Published name not indexed", matches.inputImage.publishedName, filepath)
                            if not matches.results:
                                error(f"No results", filepath)
                            for match in matches.results:
                                validate(match.image, filepath)
                                files = match.image.files
                                if isinstance(match, model.CDSMatch):
                                    if not files.ColorDepthMipInput:
                                        error("Missing ColorDepthMipInput", match.image.id, filepath)
                                    if not files.ColorDepthMipMatch:
                                        error("Missing ColorDepthMipMatch", match.image.id, filepath)
                                if isinstance(match, model.PPPMatch):
                                    if not files.ColorDepthMipSkel:
                                        error("Missing ColorDepthMipSkel", match.image.id, filepath)
                                    if not files.SignalMip:
                                        error("Missing SignalMip", match.image.id, filepath)
                                    if not files.SignalMipMasked:
                                        error("Missing SignalMipMasked", match.image.id, filepath)
                                    if not files.SignalMipMaskedSkel:
                                        error("Missing SignalMipMaskedSkel", match.image.id, filepath)
                                if validatePublishedNames and match.image.publishedName not in publishedNames:
                                    err("Match published name not indexed", match.image.publishedName, filepath)
                            c += 1
                    print(f"    Checked {c} matches")
        finally:
            for error,count in error_counts:
                print(f"{error}: {count}")

    else:
        parser.print_help(sys.stderr)
