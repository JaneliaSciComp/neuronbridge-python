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
from typing import Set, DefaultDict
from collections import defaultdict

import ray
import pydantic
import rapidjson

import neuronbridge.model as model


DEBUG = False
BATCH_SIZE = 1000
DEFAULT_VERSION = "3.4.0"

class Counter:
    """ This class keeps track of validation errors and allows for the 
        union of multiple Counter objects to represent the validation
        state of an entire data set.
    """

    def __init__(self, counts:DefaultDict[str, int]=None, errors:Set[str]=None, max_logs:int=None):
        self.counts = counts or defaultdict(int)
        self.errors = errors or set()
        self.max_logs = max_logs


    def count(self, s:str, value=1):
        """ Increment the count for a message
        """
        self.counts[s] += value


    def warn(self, s:str, *tags:str, trace:str=None):
        """ Log a warning to STDERR and keep a count of the warning type.
            Warnings do not produce a failed validation. 
        """
        if self.max_logs is None or self.counts[s] < self.max_logs:
            print(f"[WARN] {s}:", *tags, file=sys.stderr)
            if trace:
                print(trace)
        self.count(s)


    def error(self, s:str, *tags:str, trace:str=None):
        """ Log an error to STDERR and keep a count of the error type.
            Errors produce a failed validation.
        """
        if self.max_logs is None or self.counts[s] < self.max_logs:
            print(f"[ERROR] {s}:", *tags, file=sys.stderr)
            if trace:
                print(trace)
        self.errors.add(s)
        self.count(s)


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
        return Counter(counts=d,
                       errors=self.errors.union(other_counter.errors),
                       max_logs=self.max_logs)


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

        errors = "yes" if self.has_errors() else "no"
        print(f"  Has Errors: {errors}")

        for key,count in cc.items():
            level = 'ERROR' if key in self.errors else 'WARN'
            print(f"  [{level}] {key}: {count}")

        print()


    def has_errors(self):
        """ Returns True if any errors have occurred, and False otherwise.
        """
        return bool(self.errors)


def validate(counts:Counter, image, filepath):
    if not image.files.CDM:
        counts.error("Missing CDM", image.id, filepath)
    if not image.files.CDMThumbnail:
        counts.error("Missing CDMThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            counts.warn("Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            counts.warn("Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            counts.warn("Missing AlignedBodySWC", image.id, filepath)


def validate_image(counts:Counter, filepath:str, published_names:Set[str]):
    with open(filepath) as f:
        obj = rapidjson.load(f)
        lookup = model.ImageLookup(**obj)
        if not lookup.results:
            counts.error("No images", filepath)
        for image in lookup.results:
            validate(counts, image, filepath)
            published_names.add(image.publishedName)


@ray.remote
def validate_image_dir(image_dir:str, max_logs:int=None):
    published_names = set()
    counts = Counter(max_logs=max_logs)
    for root, _, files in os.walk(image_dir):
        if DEBUG: print(f"Validating images from {root}")
        for filename in files:
            tic = time.perf_counter()
            filepath = root+"/"+filename
            try:
                validate_image(counts, filepath, published_names)
            except pydantic.ValidationError:
                counts.error("Validation failed for image", filepath, trace=traceback.format_exc())
                counts.count("Exceptions")
            counts.count("Items")
            counts.count("Elapsed", value=time.perf_counter()-tic)
    counts.print_summary(f"Summary for image dir {image_dir}:")
    return {'published_names':published_names,'counts':counts}


def validate_match(filepath:str, counts:Counter, published_names:Set[str]=None):
    tic = time.perf_counter()
    with open(filepath) as f:
        obj = rapidjson.load(f)
        matches = model.PrecomputedMatches(**obj)
        validate(counts, matches.inputImage, filepath)
        if published_names and matches.inputImage.publishedName not in published_names:
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
            if published_names and match.image.publishedName not in published_names:
                counts.error("Match published name not indexed", match.image.publishedName, filepath)
            counts.count("Num Matches")
        counts.count("Items")
        counts.count("Elapsed", value=time.perf_counter()-tic)


@ray.remote
def validate_matches(match_files, published_names:Set[str]=None, max_logs:int=None):
    counts = Counter(max_logs=max_logs)
    for filepath in match_files:
        try:
            validate_match(filepath, counts, published_names)
        except pydantic.ValidationError:
            counts.error("Validation failed for match", filepath, trace=traceback.format_exc())
            counts.count("Exceptions")
    return counts


@ray.remote
def validate_match_dir(match_dir, one_batch, published_names:Set[str]=None, max_logs:int=None):

    unfinished = []
    if DEBUG: print(f"Validating matches from {match_dir}")
    for root, _, files in os.walk(match_dir):
        c = 0
        batch = []
        for filename in files:
            filepath = root+"/"+filename
            batch.append(filepath)
            if len(batch)==BATCH_SIZE:
                unfinished.append(validate_matches.remote(batch,
                                                          published_names=published_names, 
                                                          max_logs=max_logs))
                batch = []
            c += 1
        if batch:
            unfinished.append(validate_matches.remote(batch, 
                                                      published_names=published_names, 
                                                      max_logs=max_logs))
        if one_batch and len(batch) > 0:
            # for testing purposes, just do one batch per match dir
            break
        if DEBUG: print(f"Validating {c} matches in {root}")

    counts = Counter(max_logs=max_logs)
    while unfinished:
        finished, unfinished = ray.wait(unfinished, num_returns=1)
        for result in ray.get(finished):
            counts = counts.sum_counts(result)

    counts.print_summary(f"Summary for match dir {match_dir}:")
    return counts


def main():

    parser = argparse.ArgumentParser(description='Validate the data and print any issues')
    parser.add_argument('-d', '--data_path', type=str, default=f"/nrs/neuronbridge/v{DEFAULT_VERSION}", \
        help='Data path to validate, which holds "brain", "vnc", etc.')
    parser.add_argument('--nolookups', dest='validateImageLookups', action='store_false', \
        help='If --nolookups, then image lookups are skipped.')
    parser.add_argument('--nomatches', dest='validateMatches', action='store_false', \
        help='If --nomatches, then the matches are skipped.')
    parser.add_argument('--cores', type=int, default=None, \
        help='Number of CPU cores to use')
    parser.add_argument('--cluster', dest='cluster_address', type=str, default=None, \
        help='Connect to existing cluster, e.g. 123.45.67.89:10001')
    parser.add_argument('--dashboard', dest='includeDashboard', action='store_true', \
        help='Run the Ray dashboard for debugging')
    parser.add_argument('--no-dashboard', dest='includeDashboard', action='store_false', \
        help='Do not run the Ray dashboard for debugging')
    parser.add_argument('--max-logs', '-l', type=int, default=100, \
        help='Number of instances per error to print to stderr (default 100)')
    parser.add_argument('--one-batch', dest='one_batch', action='store_true', \
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

    if one_batch:
        print("Running a single batch per match dir. This mode should only be used for testing!")

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
        published_names = set()
        counts  = Counter(max_logs=max_logs)
        unfinished = []

        if args.match_file:
            batch = [args.match_file]
            counts = ray.get(validate_matches.remote(batch, max_logs=max_logs))
        else:
            if args.validateImageLookups:
                print("Validating image lookups...")
                for image_dir in image_dirs:
                    unfinished.append(validate_image_dir.remote(image_dir, max_logs))
                while unfinished:
                    finished, unfinished = ray.wait(unfinished, num_returns=1)
                    for result in ray.get(finished):
                        published_names.update(result['published_names'])
                        counts = counts.sum_counts(result['counts'])
                if DEBUG:
                    print(f"Indexed {len(published_names)} published names")

            if args.validateMatches:
                print("Validating matches...")
                for match_dir in match_dirs:
                    p_names = published_names if args.validateImageLookups else None
                    unfinished.append(validate_match_dir.remote(match_dir,
                                                                one_batch,
                                                                published_names=p_names,
                                                                max_logs=max_logs))
                    while unfinished:
                        finished, unfinished = ray.wait(unfinished, num_returns=1)
                        for result in ray.get(finished):
                            counts = counts.sum_counts(result)

    finally:
        counts.print_summary("Issue summary:")

    return 1 if counts.has_errors() else 0


if __name__ == '__main__':
    sys.exit(main())
