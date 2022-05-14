#!/usr/bin/env python
# To use the dashboard on a remote server:
#   ssh -L 8265:0.0.0.0:8265 <server address>
#   run validate.py
#   open http://localhost:8265 in your browser

import os
import sys
import time
import argparse
import rapidjson
import neuronbridge.model as model
import ray

default_data_version = "3.0.0-alpha"
max_logs = 0
debug_time = True

def inc_count(counts, s, value=1):
    if s in counts:
        counts[s] += value
    else:
        counts[s] = value


def sum_counts(a, b):
    c = dict((k,a[k]+v) for k,v in b.items() if k in a)
    d = a.copy()
    d.update(b)
    d.update(c)
    return d


def error(counts, s, *tags):
    inc_count(counts, s)
    if counts[s] < max_logs:
        print(f"{s}:", *tags, file=sys.stderr)
    if counts[s] == max_logs:
        print(f"Reached maximum logging count for '{s}'", file=sys.stderr)


def validate(counts, image, filepath):
    if not image.files.ColorDepthMip:
        error(counts, "Missing ColorDepthMip", image.id, filepath)
    if not image.files.ColorDepthMipThumbnail:
        error(counts, "Missing ColorDepthMipThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            error(counts, "Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            error(counts, "Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            error(counts, "Missing AlignedBodySWC", image.id, filepath)


def validate_image(filepath, counts, publishedNames):
    with open(filepath) as f:
        obj = rapidjson.load(f)
        lookup = model.ImageLookup(**obj)
        if not lookup.results:
            error(error_counts, f"No images")
        for image in lookup.results:
            validate(counts, image, filepath)
            publishedNames.add(image.publishedName)
        inc_count(counts, "Num Images")


@ray.remote
def validate_image_dir(image_dir):
    publishedNames = set()
    counts = {}
    for root, dirs, files in os.walk(image_dir):
        print(f"Validating images from {root}")
        for filename in files:
            filepath = root+"/"+filename
            validate_image(filepath, counts, publishedNames)
    print(f"Summary for {image_dir}:")
    if counts:
        for error,count in counts.items():
            print(f"  {error}: {count}")
    else:
        print("No issues found")
    return {'publishedNames':publishedNames,'counts':counts}


def validate_match(filepath, counts, publishedNames=None):
    tic = time.perf_counter()
    with open(filepath) as f:
        obj = rapidjson.load(f)
        matches = model.Matches(**obj)
        validate(counts, matches.inputImage, filepath)
        if publishedNames and matches.inputImage.publishedName not in publishedNames:
            error(counts, f"Published name not indexed", matches.inputImage.publishedName, filepath)
        for match in matches.results:
            validate(counts, match.image, filepath)
            files = match.image.files
            if isinstance(match, model.CDSMatch):
                if not files.ColorDepthMipInput:
                    error(counts, "Missing ColorDepthMipInput", match.image.id, filepath)
                if not files.ColorDepthMipMatch:
                    error(counts, "Missing ColorDepthMipMatch", match.image.id, filepath)
            if isinstance(match, model.PPPMatch):
                if not files.ColorDepthMipSkel:
                    error(counts, "Missing ColorDepthMipSkel", match.image.id, filepath)
                if not files.SignalMip:
                    error(counts, "Missing SignalMip", match.image.id, filepath)
                if not files.SignalMipMasked:
                    error(counts, "Missing SignalMipMasked", match.image.id, filepath)
                if not files.SignalMipMaskedSkel:
                    error(counts, "Missing SignalMipMaskedSkel", match.image.id, filepath)
            if publishedNames and match.image.publishedName not in publishedNames:
                error(counts, "Match published name not indexed", match.image.publishedName, filepath)
            inc_count(counts, "Num Matches")
        inc_count(counts, "Items")
        toc = time.perf_counter()
        inc_count(counts, "Elapsed", value=toc-tic)

@ray.remote
def validate_matches(match_files, publishedNames=None):
    counts = {}
    for filepath in match_files:
        validate_match(filepath, counts, publishedNames)
    return counts


@ray.remote
def validate_match_dir(match_dir, publishedNames=None):

    unfinished = []
    print(f"Validating matches from {match_dir}")
    for root, dirs, files in os.walk(match_dir):
        c = 0
        batch = []
        for filename in files:
            filepath = root+"/"+filename
            batch.append(filepath)
            if len(batch)==5000:
                unfinished.append(validate_matches.remote(batch, publishedNames))
                batch = []
            c += 1
        if batch:
            unfinished.append(validate_matches.remote(batch, publishedNames))
        print(f"Validating {c} matches in {root}")

    counts = {}
    while unfinished:
        finished, unfinished = ray.wait(unfinished, num_returns=1)
        for result in ray.get(finished):
            counts = sum_counts(counts, result)

    print(f"Summary for {match_dir}:")

    avg_elapsed = counts['Elapsed'] / counts['Items']
    if debug_time: print(f"  Elapsed: {avg_elapsed:0.4f} seconds on average")

    if counts:
        for error,count in counts.items():
            print(f"  {error}: {count}")
    else:
        print("  No issues found")

    return counts



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Validate the data and print any issues')
    parser.add_argument('-d', '--data_version', dest='data_version', type=str, \
        default=default_data_version, help='Data version to validate, found under /nrs/neuronbridge/v<data_version>')
    parser.add_argument('--nolookups', dest='validateImageLookups', action='store_false', \
        help='If --nolookups, then image lookups are skipped and only matches are validated.')
    parser.add_argument('--cores', dest='cores', type=int, default=None, \
        help='Number of CPU cores to use')
    parser.add_argument('--cluster', dest='cluster_address', type=str, default=None, \
        help='Connect to existing cluster, e.g. 123.45.67.89:10001')
    parser.set_defaults(validateImageLookups=True)
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

    cpus = args.cores
    if cpus:
        print(f"Using {cpus} cores")

    if "head_node" in os.environ:
        head_node = os.environ["head_node"]
        port = os.environ["port"]
        address = f"ray://{head_node}:{port}"
        ray.init(address=head_node+":"+port)
    else:
        address = f"ray://{args.cluster_address}" if args.cluster_address else None

    if address:
        print(f"Using existing cluster: {address}")
    ray.init(num_cpus=cpus, dashboard_port=8265, address=address)

    try:
        publishedNames = set()
        counts, unfinished = {}, []

        if args.validateImageLookups:
            for image_dir in image_dirs:
                unfinished.append(validate_image_dir.remote(image_dir))
            while unfinished:
                finished, unfinished = ray.wait(unfinished, num_returns=1)
                for result in ray.get(finished):
                    publishedNames.update(result['publishedNames'])
                    counts = sum_counts(counts, result['counts'])
            print(f"Indexed {len(publishedNames)} published names")

        for match_dir in match_dirs:
            unfinished.append(validate_match_dir.remote(match_dir, \
                    publishedNames if args.validateImageLookups else None))
            while unfinished:
                finished, unfinished = ray.wait(unfinished, num_returns=1)
                for result in ray.get(finished):
                    counts = sum_counts(counts, result)


    finally:
        print()
        print("Validation complete. Issue summary:")
        for error,count in counts.items():
            print(f"{error}: {count}")
        print()

