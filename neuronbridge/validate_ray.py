#!/usr/bin/env python
"""
This program validates a NeuronBridge metadata set. 

The image metadata is validated first, and all the published names are kept 
in a set in memory. Then the matches are validated, and each item in the 
matches is checked to make sure its publishedName exists in the set.

The validation can be run on a single host like this:
./neuronbridge/validate_ray.py --cores 40 --max-logs 5

To use the dashboard on a remote server:
   ssh -L 8265:0.0.0.0:8265 <server address>
   run validate_ray.py
   open http://localhost:8265 in your browser
"""

import os
import gc
import sys
import argparse
import traceback
from typing import Set, DefaultDict, List
from collections import defaultdict

from tqdm import tqdm
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

    def __init__(self, warnings:DefaultDict[str, int]=None, errors:Set[str]=None, log_file:str=None):
        self.log_file = log_file
        self.warnings = warnings if warnings else defaultdict(int)
        self.errors = errors if errors else defaultdict(int)
        

    def __enter__(self):
        """ Open the log file if it was specified.
        """
        if self.log_file:
            # Use line buffering to ensure that each log message is written immediately
            self.file_handle = open(self.log_file, "a", buffering=1)
        else:
            self.file_handle = sys.stderr
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Close the log file if it was opened.
        """ 
        if self.file_handle and self.file_handle != sys.stderr:
            self.file_handle.close()


    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle file_handle
        if "file_handle" in state:
            del state["file_handle"]
        return state


    def __setstate__(self, state):
        self.__dict__.update(state)
        # Add file_handle back since it doesn't exist in the pickle
        self.file_handle = sys.stderr


    def warn(self, s:str, *tags:str):
        """ Log a warning to STDERR and keep a count of the warning type.
            Warnings do not produce a failed validation. 
        """
        print(f"[WARN] {s}:", *tags, file=self.file_handle)
        self.warnings[s] += 1


    def error(self, s:str, *tags:str, trace:str=None):
        """ Log an error to STDERR and keep a count of the error type.
            Errors produce a failed validation.
        """
        print(f"[ERROR] {s}:", *tags, file=self.file_handle)
        if trace:
            print(trace, file=self.file_handle)
        self.errors[s] += 1


@ray.remote
class CounterActor(Counter):
    """ This class keeps track of validation errors and allows for the 
        union of multiple Counter objects to represent the validation
        state of an entire data set.
    """

    def __init__(self):
        super().__init__()
       

    def add_counts(self, counter:Counter):
        """ Add the counts from the given counter.
            TODO: after we upgrade to Python 3.11, we can use 
                  the Self type for this method signature
        """
        for key, count in counter.warnings.items():
            self.warnings[key] += count
        for key, count in counter.errors.items():
            self.errors[key] += count
    

    def has_errors(self):
        """ Returns True if any errors have occurred, and False otherwise.
        """
        return bool(self.errors)


    def print_summary(self, title:str):
        """ Print a summary of the counts and elapsed times 
            stored in a counter dict.
        """
        print()
        print(title)

        errors = "yes" if self.has_errors() else "no"
        print(f"  Has Errors: {errors}")

        for key,count in self.errors.items():
            print(f"  [ERROR] {key}: {count}")

        for key,count in self.warnings.items():
            print(f"  [WARN] {key}: {count}")

        print()


def validate(counter:Counter, image, filepath):
    if not image.files.CDM:
        counter.error("Missing CDM", image.id, filepath)
    if not image.files.CDMThumbnail:
        counter.error("Missing CDMThumbnail", image.id, filepath)
    if isinstance(image, model.LMImage):
        if not image.files.VisuallyLosslessStack:
            counter.warn("Missing VisuallyLosslessStack", image.id, filepath)
        if not image.mountingProtocol:
            counter.warn("Missing mountingProtocol", image.id, filepath)
    if isinstance(image, model.EMImage):
        if not image.files.AlignedBodySWC:
            counter.warn("Missing AlignedBodySWC", image.id, filepath)


def validate_image(counter:Counter, filepath:str, published_names:Set[str]):
    with open(filepath) as f:
        obj = rapidjson.load(f)
        lookup = model.ImageLookup(**obj)
        if not lookup.results:
            counter.error("No images", filepath)
        for image in lookup.results:
            validate(counter, image, filepath)
            published_names.add(image.publishedName)


@ray.remote
def validate_image_dir(image_dir:str, counter_actor: CounterActor, log_dir:str=None):
    worker_id = ray.get_runtime_context().get_worker_id()[:16]
    log_file = f"{log_dir}/validate_image_dir_{worker_id}.log"
    with Counter(log_file=log_file) as counter:
        published_names = set()

        for root, _, files in os.walk(image_dir):
            if DEBUG: print(f"Validating images from {root}")
            for filename in files:
                filepath = root+"/"+filename
                try:
                    validate_image(counter, filepath, published_names)
                except pydantic.ValidationError:
                    counter.error("Validation failed for image", filepath, trace=traceback.format_exc())
        
        counter_actor.add_counts.remote(counter)
        counter_actor.print_summary.remote(f"Totals after validation of image dir {image_dir}:")
        
        for published_name in published_names:
            print(published_name, file=counter.file_handle)

        return published_names


def validate_match(filepath:str, counter:Counter, published_names:Set[str]=None):
    with open(filepath) as f:
        obj = rapidjson.load(f)
        matches = model.PrecomputedMatches(**obj)
        validate(counter, matches.inputImage, filepath)
        if published_names and matches.inputImage.publishedName not in published_names:
            counter.error("Published name not indexed", matches.inputImage.publishedName, filepath)
        for match in matches.results:
            validate(counter, match.image, filepath)
            files = match.files
            if isinstance(match, model.CDSMatch):
                if not files.CDMInput:
                    counter.error("Missing CDMInput", match.image.id, filepath)
                if not files.CDMMatch:
                    counter.error("Missing CDMMatch", match.image.id, filepath)
            if isinstance(match, model.PPPMatch):
                if not files.CDMSkel:
                    counter.error("Missing CDMSkel", match.image.id, filepath)
                if not files.SignalMip:
                    counter.error("Missing SignalMip", match.image.id, filepath)
                if not files.SignalMipMasked:
                    counter.error("Missing SignalMipMasked", match.image.id, filepath)
                if not files.SignalMipMaskedSkel:
                    counter.error("Missing SignalMipMaskedSkel", match.image.id, filepath)
            if published_names and match.image.publishedName not in published_names:
                counter.error("Match published name not indexed", match.image.publishedName, filepath)


@ray.remote
def validate_matches(root_dir:str, match_files:List[str], counter_actor: CounterActor, published_names:Set[str]=None, log_dir:str=None):
    worker_id = ray.get_runtime_context().get_worker_id()[:16]
    log_file = f"{log_dir}/validate_matches_{worker_id}.log"
    with Counter(log_file=log_file) as counter:
        for filename in match_files:
            filepath = root_dir+"/"+filename
            try:
                validate_match(filepath, counter, published_names)
            except pydantic.ValidationError:
                counter.error("Validation failed for match", filepath, trace=traceback.format_exc())
        counter_actor.add_counts.remote(counter)

    gc.collect()


def validate_match_dir(match_dir, one_batch, counter_actor: CounterActor, published_names:Set[str]=None, log_dir:str=None):
    unfinished = []
    print(f"Validating matches in {match_dir}")
    for root, _, files in os.walk(match_dir):
        c = 0
        batch = []
        for filename in files:
            batch.append(filename)
            if len(batch)==BATCH_SIZE:
                unfinished.append(validate_matches.remote(root,batch, counter_actor, 
                                                          published_names=published_names,
                                                          log_dir=log_dir))
                batch = []
            c += 1
        if batch:
            unfinished.append(validate_matches.remote(root, batch, counter_actor, 
                                                      published_names=published_names,
                                                      log_dir=log_dir))
            
        if one_batch and len(batch) > 0:
            # for testing purposes, just do one batch per match dir
            break
        
        print(f"Validating {c} matches in {root}")
    
    total = len(unfinished)
    with tqdm(total=total, desc="Processing matches") as pbar:
        while unfinished:
            _, unfinished = ray.wait(unfinished, num_returns=1)
            pbar.update(1)

    counter_actor.print_summary.remote(f"Totals after validation of match dir {match_dir}:")


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
    parser.add_argument('--one-batch', dest='one_batch', action='store_true', \
        help='Do only one batch of match validation (for testing)')
    parser.add_argument('--match', dest='match_file', type=str, default=None, \
        help='Only validate the given match file')
    parser.add_argument('--log-dir', dest='log_dir', type=str, default="logs", \
        help='Directory to store log files')

    parser.set_defaults(validateImageLookups=True)
    parser.set_defaults(validateMatches=True)
    parser.set_defaults(includeDashboard=False)
    parser.set_defaults(one_batch=False)

    args = parser.parse_args()
    data_path = args.data_path
    one_batch = args.one_batch

    if one_batch:
        print("Running a single batch per match dir. This mode should only be used for testing!")

    image_dirs = [
        f"{data_path}/brain+vnc/mips/embodies",
        f"{data_path}/brain+vnc/mips/lmlines",
    ]

    match_dirs = [
        f"{data_path}/brain/cdmatches/lm-vs-em/",
        f"{data_path}/brain/cdmatches/em-vs-lm/",
        f"{data_path}/brain/pppmatches/em-vs-lm/",
        f"{data_path}/vnc/cdmatches/lm-vs-em/",
        f"{data_path}/vnc/cdmatches/em-vs-lm/",
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

    kwargs = {}
    if include_dashboard:
        kwargs["include_dashboard"] = include_dashboard
        kwargs["dashboard_host"] = "0.0.0.0"
        kwargs["dashboard_port"] = dashboard_port

    ray.init(num_cpus=cpus, address=address, **kwargs)

    # Ensure the log directory exists
    os.makedirs(args.log_dir, exist_ok=True)

    try:
        published_names = set()
        unfinished = []
        
        counter_actor = CounterActor.remote()
        
        if args.match_file:
            match_dir = os.path.dirname(args.match_file)
            match_filename = os.path.basename(args.match_file)
            batch = [match_filename]
            ray.get(validate_matches.remote(match_dir, batch, counter_actor, log_dir=args.log_dir))
        else:
            if args.validateImageLookups:
                print("Validating image lookups...")
                for image_dir in image_dirs:
                    print(f"Validating image lookups in {image_dir}")
                    unfinished.append(validate_image_dir.remote(image_dir, counter_actor, log_dir=args.log_dir))
                while unfinished:
                    finished, unfinished = ray.wait(unfinished, num_returns=1)
                    for result in ray.get(finished):
                        published_names.update(result)
                print(f"Indexed {len(published_names)} published names")

            if args.validateMatches:
                print("Validating matches...")
                for match_dir in match_dirs:
                    print(f"Validating matches in {match_dir}")
                    p_names = published_names if args.validateImageLookups else None
                    validate_match_dir(match_dir,
                                       one_batch,
                                       counter_actor,
                                       published_names=p_names,
                                       log_dir=args.log_dir)

    finally:
        counter_actor.print_summary.remote("Final totals:")

    return 1 if counter_actor.has_errors.remote() else 0


if __name__ == '__main__':
    sys.exit(main())
