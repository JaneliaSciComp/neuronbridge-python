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
import sys
import argparse
from typing import Set, List
from collections import defaultdict

import ray
from tqdm import tqdm

# Default version of the data to validate
DEFAULT_VERSION = "3.4.0"

# Number of matches to send to a worker to process in a single batch
BATCH_SIZE = 100


@ray.remote
class CounterActor:
    """ This class keeps track of validation errors and allows for the 
        union of multiple Counter objects to represent the validation
        state of an entire data set.
    """

    def __init__(self):
        self.warnings = defaultdict(int)
        self.errors = defaultdict(int)
       

    def add_counts(self, counter):
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


@ray.remote
def validate_image_dir_remote(root_dir:str, batch:List[str], counter_actor):
    from neuronbridge.validate_worker import validate_image_dir_batch
    return validate_image_dir_batch(root_dir, batch, counter_actor)


@ray.remote
def validate_matches_remote(root_dir:str, batch:List[str], counter_actor, published_names:Set[str]=None):
    from neuronbridge.validate_worker import validate_matches_batch
    return validate_matches_batch(root_dir, batch, counter_actor, published_names=published_names)


def validate_image_dir(image_dir:str, one_batch:bool, counter_actor:CounterActor):
    published_names = set()
    unfinished = []
    print(f"Walking image dir {image_dir}")
    for root, _, files in os.walk(image_dir):
        c = 0
        batch = []
        for filename in files:
            batch.append(filename)
            if len(batch)==BATCH_SIZE:
                unfinished.append(validate_image_dir_remote.remote(root, batch, counter_actor))
                batch = []
                if one_batch:
                    break
            c += 1

        if batch:
            unfinished.append(validate_image_dir_remote.remote(root, batch, counter_actor))
        
        print(f"Validating {c} image lookups in {root}")
    
    total = len(unfinished)
    with tqdm(total=total, desc="Processing image lookups") as pbar:
        while unfinished:
            finished, unfinished = ray.wait(unfinished, num_returns=1)
            for result in ray.get(finished):
                published_names.update(result)
            pbar.update(1)

    counter_actor.print_summary.remote(f"Totals after validation of image dir {image_dir}:")
    return published_names


def validate_match_dir(match_dir, one_batch, counter_actor: CounterActor, published_names:Set[str]=None):
    unfinished = []
    print(f"Walking match dir {match_dir}")
    for root, _, files in os.walk(match_dir):
        c = 0
        batch = []
        for filename in files:
            batch.append(filename)
            if len(batch)==BATCH_SIZE:
                unfinished.append(validate_matches_remote.remote(root,batch, counter_actor, published_names=published_names))
                batch = []
                if one_batch:
                    break
            c += 1
            
        if batch:
            unfinished.append(validate_matches_remote.remote(root, batch, counter_actor, published_names=published_names))
        
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

    kwargs = {}
    if include_dashboard:
        kwargs["include_dashboard"] = include_dashboard
        kwargs["dashboard_host"] = "0.0.0.0"
        kwargs["dashboard_port"] = dashboard_port

    ray.init(num_cpus=cpus, address=address, ignore_reinit_error=True, **kwargs)

    try:
        published_names = set()
        
        counter_actor = CounterActor.remote()
        
        if args.match_file:
            match_dir = os.path.dirname(args.match_file)
            match_filename = os.path.basename(args.match_file)
            batch = [match_filename]
            ray.get(validate_matches_remote.remote(match_dir, batch, counter_actor))
        else:
            if args.validateImageLookups:
                print("Validating image lookups...")
                for image_dir in image_dirs:
                    print(f"Validating image lookups in {image_dir}")
                    result = validate_image_dir(image_dir, one_batch, counter_actor)
                    published_names.update(result)
                                        
                print(f"Indexed {len(published_names)} total published names")

            if args.validateMatches:
                print("Validating matches...")
                for match_dir in match_dirs:
                    p_names = published_names if args.validateImageLookups else None
                    validate_match_dir(match_dir, one_batch, counter_actor, p_names)

    finally:
        counter_actor.print_summary.remote("Final totals:")

    return 1 if counter_actor.has_errors.remote() else 0


if __name__ == '__main__':
    sys.exit(main())
