#!/usr/bin/env python
# To use the dashboard on a remote server:
#   ssh -L 8265:0.0.0.0:8265 <server address>
#   run validate.py
#   open http://localhost:8265 in your browser

import os
import sys
import time
import argparse
import traceback

import rapidjson
import neuronbridge.model as model
import ray

default_data_version = "3.0.0-alpha"
max_logs = 0
debug = False
batch_size = 1000

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


def print_summary(title, counts):
    print()
    print(title)
    cc = counts.copy()
    if 'Elapsed' in cc and 'Items' in cc:
        mean_elapsed = cc['Elapsed'] / cc['Items']
        print(f"  Items: {cc['Items']}")
        print(f"  Elapsed: {mean_elapsed:0.4f} seconds (on avg per item)")
        del cc['Items']
        del cc['Elapsed']
    for error,count in cc.items():
        print(f"  {error}: {count}")



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
            error(counts, f"No images")
        for image in lookup.results:
            validate(counts, image, filepath)
            publishedNames.add(image.publishedName)


@ray.remote
def validate_image_dir(image_dir):
    publishedNames = set()
    counts = {}
    for root, dirs, files in os.walk(image_dir):
        if debug: print(f"Validating images from {root}")
        for filename in files:
            tic = time.perf_counter()
            filepath = root+"/"+filename
            try:
                validate_image(filepath, counts, publishedNames)
            except Exception as e:
                trace = traceback.format_exc()
                print("Error validating", filepath)
                print(trace)
                inc_count(counts, "Exceptions")
            inc_count(counts, "Items")
            inc_count(counts, "Elapsed", value=time.perf_counter()-tic)
    print_summary(f"Summary for {image_dir}:", counts)
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
        inc_count(counts, "Elapsed", value=time.perf_counter()-tic)

@ray.remote
def validate_matches(match_files, publishedNames=None):
    counts = {}
    for filepath in match_files:
        try:
            validate_match(filepath, counts, publishedNames)
        except Exception as e:
            trace = traceback.format_exc()
            print("Error validating", filepath)
            print(trace)
            inc_count(counts, "Exceptions")
    return counts


@ray.remote
def validate_match_dir(match_dir, publishedNames=None):

    unfinished = []
    if debug: print(f"Validating matches from {match_dir}")
    for root, dirs, files in os.walk(match_dir):
        c = 0
        batch = []
        for filename in files:
            filepath = root+"/"+filename
            batch.append(filepath)
            if len(batch)==batch_size:
                unfinished.append(validate_matches.remote(batch, publishedNames))
                batch = []
            c += 1
        if batch:
            unfinished.append(validate_matches.remote(batch, publishedNames))
        if debug: print(f"Validating {c} matches in {root}")

    counts = {}
    while unfinished:
        finished, unfinished = ray.wait(unfinished, num_returns=1)
        for result in ray.get(finished):
            counts = sum_counts(counts, result)

    print_summary(f"Summary for {match_dir}:", counts)
    return counts


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Validate the data and print any issues')
    parser.add_argument('-d', '--data_version', dest='data_version', type=str, \
        default=default_data_version, help='Data version to validate, found under /nrs/neuronbridge/v<data_version>')
    parser.add_argument('--nolookups', dest='validateImageLookups', action='store_false', \
        help='If --nolookups, then image lookups are skipped.')
    parser.add_argument('--nomatches', dest='validateMatches', action='store_false', \
        help='If --nomatches, then the matches are skipped.')
    parser.add_argument('--cores', dest='cores', type=int, default=None, \
        help='Number of CPU cores to use')
    parser.add_argument('--cluster', dest='cluster_address', type=str, default=None, \
        help='Connect to existing cluster, e.g. 123.45.67.89:10001')
    parser.add_argument('--dashboard', dest='includeDashboard', action='store_true', \
        help='Run the Ray dashboard for debugging')
    parser.add_argument('--no-dashboard', dest='includeDashboard', action='store_false', \
        help='Do not run the Ray dashboard for debugging')
    
    parser.set_defaults(validateImageLookups=True)
    parser.set_defaults(validateMatches=True)
    parser.set_defaults(includeDashboard=False)
    
    args = parser.parse_args()
    data_version = args.data_version

    if data_version == "3.0.0-alpha":
        # For the alpha model, the directory structure was inherited from the older models.
        # This can be deleted once we merge this code into the main branch.
        image_dirs = [
            f"/nrs/neuronbridge/v{data_version}/brain/mips/em_bodies",
            f"/nrs/neuronbridge/v{data_version}/brain/mips/all_mcfo_lines",
            f"/nrs/neuronbridge/v{data_version}/brain/mips/split_gal4_lines",
            f"/nrs/neuronbridge/v{data_version}/vnc/mips/em_bodies",
            f"/nrs/neuronbridge/v{data_version}/vnc/mips/gen1_mcfo_lines",
            f"/nrs/neuronbridge/v{data_version}/vnc/mips/split_gal4_lines_published",
        ]
        match_dirs = [
            f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flyem-vs-flylight",
            f"/nrs/neuronbridge/v{data_version}/brain/cdsresults.final/flylight-vs-flyem",
            f"/nrs/neuronbridge/v{data_version}/brain/pppresults/flyem-to-flylight.public",
            f"/nrs/neuronbridge/v{data_version}/vnc/cdsresults.final/flyem-vs-flylight",
            f"/nrs/neuronbridge/v{data_version}/vnc/cdsresults.final/flylight-vs-flyem",
            f"/nrs/neuronbridge/v{data_version}/vnc/pppresults/flyem-to-flylight.public",
        ]
    else:
        image_dirs = [
            f"/nrs/neuronbridge/v{data_version}/brain/mips/embodies",
            f"/nrs/neuronbridge/v{data_version}/brain/mips/lmlines",
            f"/nrs/neuronbridge/v{data_version}/vnc/mips/embodies",
            f"/nrs/neuronbridge/v{data_version}/vnc/mips/lmlines",
        ]
        match_dirs = [
            f"/nrs/neuronbridge/v{data_version}/brain/cdmatches/em-vs-lm/",
            f"/nrs/neuronbridge/v{data_version}/brain/cdmatches/lm-vs-em/",
            f"/nrs/neuronbridge/v{data_version}/brain/pppmatches/em-vs-lm/",
            f"/nrs/neuronbridge/v{data_version}/vnc/cdmatches/em-vs-lm/",
            f"/nrs/neuronbridge/v{data_version}/vnc/cdmatches/lm-vs-em/",
            f"/nrs/neuronbridge/v{data_version}/vnc/pppmatches/em-vs-lm/",
        ]

    cpus = args.cores
    if cpus:
        print(f"Using {cpus} cores")

    if "head_node" in os.environ:
        head_node = os.environ["head_node"]
        port = os.environ["port"]
        address = f"{head_node}:{port}"
    else:
        address = f"{args.cluster_address}" if args.cluster_address else None

    if address:
        print(f"Using cluster: {address}")

    include_dashboard = args.includeDashboard
    dashboard_port = 8265
    if include_dashboard:
        print(f"Deploying dashboard on port {dashboard_port}")

    ray.init(num_cpus=cpus,
            include_dashboard=include_dashboard,
            dashboard_port=dashboard_port,
            address=address)

    try:
        publishedNames = set()
        counts, unfinished = {}, []

        if args.validateImageLookups:
            print("Validating image lookups...")
            for image_dir in image_dirs:
                unfinished.append(validate_image_dir.remote(image_dir))
            while unfinished:
                finished, unfinished = ray.wait(unfinished, num_returns=1)
                for result in ray.get(finished):
                    publishedNames.update(result['publishedNames'])
                    counts = sum_counts(counts, result['counts'])
            if debug: print(f"Indexed {len(publishedNames)} published names")

        if args.validateMatches:
            print("Validating matches...")
            for match_dir in match_dirs:
                unfinished.append(validate_match_dir.remote(match_dir, \
                        publishedNames if args.validateImageLookups else None))
                while unfinished:
                    finished, unfinished = ray.wait(unfinished, num_returns=1)
                    for result in ray.get(finished):
                        counts = sum_counts(counts, result)

    finally:
        print_summary("Validation complete. Issue summary:", counts)

