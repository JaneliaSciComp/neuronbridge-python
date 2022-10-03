#!/usr/bin/env python
import os
import sys
import argparse
import rapidjson
import neuronbridge.model as model

default_data_version = "3.0.0"


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


def validate(image, filepath):
    if not image.files.CDM:
        error("Missing CDM", image.id, filepath)
    if not image.files.CDMThumbnail:
        error("Missing CDMThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            error("Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            error("Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            error("Missing AlignedBodySWC", image.id, filepath)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Validate the data and print any issues')
    parser.add_argument('-d', '--data_version', dest='data_version', type=str, \
        default=default_data_version, help='Data version to validate, found under /nrs/neuronbridge/v<data_version>')
    parser.add_argument('--nolookups', dest='validateImageLookups', action='store_false', \
        help='If --nolookups, then image lookups are skipped and only matches are validated.')
    parser.add_argument('--nonames', dest='validatePublishedNames', action='store_false', \
        help='If --nonames, then published names are not validated.')
    parser.set_defaults(validateImageLookups=True)
    parser.set_defaults(validatePublishedNames=True)
    args = parser.parse_args()
    data_version = args.data_version

    image_dirs = [
        f"/nrs/neuronbridge/v{data_version}/brain/mips/em_bodies",
        f"/nrs/neuronbridge/v{data_version}/brain/mips/all_mcfo_lines",
        f"/nrs/neuronbridge/v{data_version}/brain/mips/split_gal4_lines",
        f"/nrs/neuronbridge/v{data_version}/vnc/mips/em_bodies",
        f"/nrs/neuronbridge/v{data_version}/vnc/mips/gen1_mcfo_lines",
        f"/nrs/neuronbridge/v{data_version}/vnc/mips/split_gal4_lines_published",
    ]
    match_dirs = [
        f"/nrs/neuronbridge/v{data_version}/vnc/cdsresults.final/flylight-vs-flyem",
        f"/nrs/neuronbridge/v{data_version}/vnc/pppresults/flyem-to-flylight.public",
        f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flyem-vs-flylight",
        f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flylight-vs-flyem",
        f"/nrs/neuronbridge/v{data_version}/brain/pppresults/flyem-to-flylight.public",
        f"/nrs/neuronbridge/v{data_version}/vnc/cdsresults.final/flyem-vs-flylight",
    ]

    try:
        publishedNames = set()
        if args.validateImageLookups:
            for image_dir in image_dirs:
                for root, dirs, files in os.walk(image_dir):
                    print(f"Validating images from {root}")
                    c = 0
                    for filename in files:
                        filepath = root+"/"+filename
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
            for root, dirs, files in os.walk(match_dir):
                print(f"Validating matches from {root}")
                c = 0
                for filename in files:
                    filepath = root+"/"+filename
                    with open(filepath) as f:
                        obj = rapidjson.load(f)
                        matches = model.Matches(**obj)
                        validate(matches.inputImage, filepath)
                        if args.validatePublishedNames and matches.inputImage.publishedName not in publishedNames:
                            error(f"Published name not indexed", matches.inputImage.publishedName, filepath)
                        for match in matches.results:
                            validate(match.image, filepath)
                            files = match.image.files
                            if isinstance(match, model.CDSMatch):
                                if not files.CDMInput:
                                    error("Missing CDMInput", match.image.id, filepath)
                                if not files.CDMMatch:
                                    error("Missing CDMMatch", match.image.id, filepath)
                            if isinstance(match, model.PPPMatch):
                                if not files.CDMSkel:
                                    error("Missing CDMSkel", match.image.id, filepath)
                                if not files.SignalMip:
                                    error("Missing SignalMip", match.image.id, filepath)
                                if not files.SignalMipMasked:
                                    error("Missing SignalMipMasked", match.image.id, filepath)
                                if not files.SignalMipMaskedSkel:
                                    error("Missing SignalMipMaskedSkel", match.image.id, filepath)
                            if args.validatePublishedNames and match.image.publishedName not in publishedNames:
                                error("Match published name not indexed", match.image.publishedName, filepath)
                        c += 1
                print(f"    Checked {c} matches")
    finally:
        print()
        for error,count in error_counts.items():
            print(f"{error}: {count}")
        print()

