import os
import gc
import sys
import traceback
from typing import Set, DefaultDict, List
from collections import defaultdict

import ray
import pydantic
import rapidjson

import neuronbridge.model as model

# Directory to store log files
LOG_DIR = "logs"

# Print debug messages on the workers
DEBUG = False

# Maximum number of log lines (per worker) to print for each warning or error type
MAX_LOGS = 1000

# Maximum number of matches allowed per published name
MAX_MATCHES_PER_NAME = 10

# Maximum number of matches allowed per file
MAX_MATCHES_PER_FILE = 5000


class Counter:
    """ This class keeps track of validation errors and allows for the 
        union of multiple Counter objects to represent the validation
        state of an entire data set.
    """

    def __init__(self, warnings:DefaultDict[str, int]=None, errors:Set[str]=None, log_file:str=None, max_logs:int=None):
        self.warnings = warnings if warnings else defaultdict(int)
        self.errors = errors if errors else defaultdict(int)
        self.log_file = log_file
        self.max_logs = max_logs
        self.tags = set()


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


    def print(self, s:str):
        """ Print a message to the log file.
        """
        print(s, file=self.file_handle)


    def warn(self, s:str, arg:str, filepath:str):
        """ Log a warning to STDERR and keep a count of the warning type.
            Warnings do not produce a failed validation. 
        """
        tag = f"{s}: {arg}"
        if tag not in self.tags:
            self.tags.add(tag)
            if not self.max_logs or self.warnings[s] <= self.max_logs:
                print(f"[WARN] {tag} {filepath}", file=self.file_handle)
        self.warnings[s] += 1


    def error(self, s:str, arg:str, filepath:str, trace:str=None):
        """ Log an error to STDERR and keep a count of the error type.
            Errors produce a failed validation.
        """
        tag = f"{s}: {arg}"
        if tag not in self.tags:
            self.tags.add(tag)
            if not self.max_logs or self.errors[s] <= self.max_logs:
                print(f"[ERROR] {tag} {filepath}", file=self.file_handle)
            if trace:
                print(trace, file=self.file_handle)
        self.errors[s] += 1


# Putting this state in a separate module is a neat little hack that I found here:
# https://discuss.ray.io/t/global-variables-to-maintain-a-worker-specific-state/12251/3
# This makes it possible to retain the worker-specific state (e.g. log file) across multiple
# remote calls to the worker.
worker_id = ray.get_runtime_context().get_worker_id()
log_file = f"{LOG_DIR}/worker_{worker_id}.log"
counter = Counter(log_file=log_file, max_logs=MAX_LOGS) 


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
            counter.error("No images", "", filepath)
        for image in lookup.results:
            validate(counter, image, filepath)
            published_names.add(image.publishedName)


def validate_image_dir_batch(root_dir:str, image_files:List[str], counter_actor):
    
    with counter:
        published_names = set()

        for filename in image_files:
            filepath = os.path.join(root_dir, filename)
            try:
                validate_image(counter, filepath, published_names)
            except pydantic.ValidationError:
                counter.error("Validation failed for image", "", filepath, trace=traceback.format_exc())
        
        counter_actor.add_counts.remote(counter)
        return published_names



def validate_match_file(filepath:str, counter:Counter, published_names:Set[str]=None):
    with open(filepath) as f:
        num_matches_per_name = defaultdict(int)
        obj = rapidjson.load(f)
        matches = model.PrecomputedMatches(**obj)
        validate(counter, matches.inputImage, filepath)
        if published_names and matches.inputImage.publishedName not in published_names:
            counter.error("Published name not indexed", matches.inputImage.publishedName, filepath)
        for match in matches.results:
            num_matches_per_name[match.image.publishedName] += 1
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

        num_matches = len(matches.results)
        if num_matches > MAX_MATCHES_PER_FILE:
            counter.warn("Too many matches", f"({num_matches})", filepath)

        for name, count in num_matches_per_name.items():
            if count > MAX_MATCHES_PER_NAME:
                counter.warn("Too many matches for published name", name, filepath)
                break


def validate_matches_batch(root_dir:str, match_files:List[str], counter_actor, published_names:Set[str]=None, log_dir:str=None):
    i = 0
    with counter:
        
        for filename in match_files:
            filepath = os.path.join(root_dir, filename)
            counter.print(f"Validating {filepath} ({i}/{len(match_files)})")
            try:
                validate_match_file(filepath, counter, published_names)
            except pydantic.ValidationError:
                counter.error("Validation failed for match", "", filepath, trace=traceback.format_exc())
            i += 1
        
        counter_actor.add_counts.remote(counter)
        
    gc.collect()
