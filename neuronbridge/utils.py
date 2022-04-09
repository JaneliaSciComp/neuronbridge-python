
from typing import List, Tuple
from neuronbridge.model import *

def get_published_name_set(matches : List[Match]) -> List[str]:
    """
    Returns a list of all the published names of the masks in the matches.
    """
    return set([match.publishedName for match in matches])


def get_ranks(matches : List[Match], published_names : List[str]) -> List[Tuple[str,int]]:
    """
    Returns a list of ranks for each published name in the matches.
    """
    all_names = [match.publishedName for match in matches]
    return { name : all_names.index(name) for name in published_names }


def get_first_match_for_name(matches : List[Match], name : str) -> Match:
    """
    Returns a list of the first images in the matches.
    """
    for match in matches:
        if match.publishedName == name:
            return match
        

