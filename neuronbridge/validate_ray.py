#!/usr/bin/env python
"""
This program validates a NeuronBridge metadata set. 

The image metadata is validated first, and all the published names are kept 
in a set in memory. Then the matches are validated, and each item in the 
matches is checked to make sure its publishedName exists in the set.

The validation can be run on a single host like this:
./neuronbridge/validate_ray.py --cores 40 --max-logs 5

To run on a cluster, you can use 

To use the dashboard on a remote server:
   ssh -L 8265:0.0.0.0:8265 <server address>
   run validate.py
   open http://localhost:8265 in your browser
"""

import os
import sys
import time
import argparse
import traceback
from typing import DefaultDict, Set
from collections import defaultdict

import ray
import pydantic
import rapidjson

import neuronbridge.model as model


debug = False
batch_size = 1000
default_data_version = "3.3.0"

class Counter:
        
    def __init__(self, counts=None, max_logs=0):
        self.counts = counts or defaultdict(int)
        self.max_logs = max_logs
        

    def count(self, s:str, value=1):
        """ Increment the count for a message
        """
        self.counts[s] += value


    def error(self, s:str, *tags:str, trace:str=None):
        """ Log an error to STDERR and keep a count of the error type.
        """
        self.count(s)
        if self.max_logs is None or self.counts[s] < self.max_logs:
            print(f"{s}:", *tags, file=sys.stderr)
            if trace:
                print(trace)


    def sum_counts(self, other_counter):
        """ Combine two counter dicts into one.
            TODO: after we upgrade to Python 3.11, we can use 
                  the Self type for this method signature
        """
        a = self.counts
        b = other_counter.counts
        c = dict((k,a[k]+v) for k,v in b.items() if k in a)
        d = a.copy()
        d.update(b)
        d.update(c)
        return Counter(counts=d, max_logs=self.max_logs)


    def print_summary(self, title:str):
        """ Print a summary of the counts and elapsed times 
            stored in a counter dict.
        """
        print()
        print(title)
        cc = self.counts.copy()
        if 'Elapsed' in cc and 'Items' in cc:
            mean_elapsed = cc['Elapsed'] / cc['Items']
            print(f"  Items: {cc['Items']}")
            print(f"  Elapsed: {mean_elapsed:0.4f} seconds (on avg per item)")
            del cc['Items']
            del cc['Elapsed']
        for error,count in cc.items():
            print(f"  {error}: {count}")



def validate(counts:Counter, image, filepath):
    if not image.files.CDM:
        counts.error("Missing CDM", image.id, filepath)
    if not image.files.CDMThumbnail:
        counts.error("Missing CDMThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            counts.error("Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            counts.error("Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            counts.error("Missing AlignedBodySWC", image.id, filepath)


def validate_image(filepath:str, counts:Counter, publishedNames:Set[str]):
    with open(filepath) as f:
        obj = rapidjson.load(f)
        lookup = model.ImageLookup(**obj)
        if not lookup.results:
            counts.error("No images", filepath)
        for image in lookup.results:
            validate(counts, image, filepath)
            publishedNames.add(image.publishedName)


@ray.remote
def validate_image_dir(image_dir:str):
    publishedNames = set()
    counts = Counter()
    for root, dirs, files in os.walk(image_dir):
        if debug: print(f"Validating images from {root}")
        for filename in files:
            tic = time.perf_counter()
            filepath = root+"/"+filename
            try:
                validate_image(filepath, counts, publishedNames)
            except pydantic.ValidationError:
                counts.error("Validation failed for image", filepath, trace=traceback.format_exc())
                counts.count("Exceptions")
            counts.count("Items")
            counts.count("Elapsed", value=time.perf_counter()-tic)
    counts.print_summary(f"Summary for {image_dir}:")
    return {'publishedNames':publishedNames,'counts':counts}


def validate_match(filepath:str, counts:Counter, publishedNames:Set[str]=None):
    tic = time.perf_counter()
    with open(filepath) as f:
        obj = rapidjson.load(f)
        matches = model.PrecomputedMatches(**obj)
        validate(counts, matches.inputImage, filepath)
        if publishedNames and matches.inputImage.publishedName not in publishedNames:
            counts.error("Published name not indexed", matches.inputImage.publishedName, filepath)
        for match in matches.results:
            validate(counts, match.image, filepath)
            files = match.files
            if isinstance(match, model.CDSMatch):
                if not files.CDMInput:
                    counts.error("Missing CDMInput", match.image.id, filepath)
                if not files.CDMMatch:
                    counts.error("Missing CDMMatch", match.image.id, filepath)
            if isinstance(match, model.PPPMatch):
                if not files.CDMSkel:
                    counts.error("Missing CDMSkel", match.image.id, filepath)
                if not files.SignalMip:
                    counts.error("Missing SignalMip", match.image.id, filepath)
                if not files.SignalMipMasked:
                    counts.error("Missing SignalMipMasked", match.image.id, filepath)
                if not files.SignalMipMaskedSkel:
                    counts.error("Missing SignalMipMaskedSkel", match.image.id, filepath)
            if publishedNames and match.image.publishedName not in publishedNames:
                counts.error("Match published name not indexed", match.image.publishedName, filepath)
            counts.count("Num Matches")
        counts.count("Items")
        counts.count("Elapsed", value=time.perf_counter()-tic)


@ray.remote
def validate_matches(match_files, publishedNames:Set[str]=None):
    counts = Counter()
    for filepath in match_files:
        try:
            validate_match(filepath, counts, publishedNames)
        except pydantic.ValidationError:
            counts.error("Validation failed for match", filepath, trace=traceback.format_exc())
            counts.count("Exceptions")
    return counts


@ray.remote
def validate_match_dir(match_dir, one_batch, publishedNames:Set[str]=None):

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
        if one_batch and len(batch) > 0:
            # for testing purposes, just do one batch per match dir
            break
        if debug: print(f"Validating {c} matches in {root}")

    counts = Counter()
    while unfinished:
        finished, unfinished = ray.wait(unfinished, num_returns=1)
        for result in ray.get(finished):
            counts = counts.sum_counts(result)

    counts.print_summary(f"Summary for {match_dir}:")
    return counts


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Validate the data and print any issues')
    parser.add_argument('-d', '--data_path', dest='data_path', type=str, default=f"/nrs/neuronbridge/v{default_data_version}", \
        help='Data path to validate, which holds "brain", "vnc", etc.')
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
    parser.add_argument('--max-logs', '-l', dest='max_logs', type=int, default=100, \
        help='Number of instances per error to print to stderr (default 100)')
    parser.add_argument('--one-batch', dest='one_batch', action='store_false', \
        help='Do only one batch of match validation (for testing)')
    parser.add_argument('--match', dest='match_file', type=str, default=None, \
        help='Only validate the given match file')

    parser.set_defaults(validateImageLookups=True)
    parser.set_defaults(validateMatches=True)
    parser.set_defaults(includeDashboard=False)
    parser.set_defaults(one_batch=False)

    args = parser.parse_args()
    data_path = args.data_path
    max_logs = args.max_logs
    one_batch = args.one_batch

    image_dirs = [
        f"{data_path}/brain+vnc/mips/embodies",
        f"{data_path}/brain+vnc/mips/lmlines",
    ]

    match_dirs = [
        f"{data_path}/brain/cdmatches/em-vs-lm/",
        f"{data_path}/brain/cdmatches/lm-vs-em/",
        f"{data_path}/brain/pppmatches/em-vs-lm/",
        f"{data_path}/vnc/cdmatches/em-vs-lm/",
        f"{data_path}/vnc/cdmatches/lm-vs-em/",
        f"{data_path}/vnc/pppmatches/em-vs-lm/",
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
        counts  = Counter(max_logs=args.max_logs)
        unfinished = []

        if args.match_file:
            batch = [args.match_file]
            ray.get(validate_matches.remote(batch))
        else:
            if args.validateImageLookups:
                print("Validating image lookups...")
                for image_dir in image_dirs:
                    unfinished.append(validate_image_dir.remote(image_dir))
                while unfinished:
                    finished, unfinished = ray.wait(unfinished, num_returns=1)
                    for result in ray.get(finished):
                        publishedNames.update(result['publishedNames'])
                        counts = counts.sum_counts(result['counts'])
                if debug:
                    print(f"Indexed {len(publishedNames)} published names")

            if args.validateMatches:
                print("Validating matches...")
                for match_dir in match_dirs:
                    unfinished.append(validate_match_dir.remote(match_dir, one_batch, \
                            publishedNames if args.validateImageLookups else None))
                    while unfinished:
                        finished, unfinished = ray.wait(unfinished, num_returns=1)
                        for result in ray.get(finished):
                            counts = counts.sum_counts(result)

    finally:
        counts.print_summary("Validation complete. Issue summary:")

