# -*- coding: utf-8 -*-
"""utility methods
"""
from itertools import izip_longest
from dolmen.sunburnt.utilities import get_solr_manager

_marker = object


def in_queries(fname, values, max_size=80, solr_manager=None):
    """this will yield queries that ar a or for a single field
    on multiple values (as something *in* set_of_values)

    This permits to be sure to have queries that are not to long
    """
    # grouper iterator, see itertools recipes
    grouper = izip_longest(fillvalue=_marker, *([iter(values)] * max_size))
    if solr_manager is None:
        solr_manager = get_solr_manager()
    for fvalues in grouper:
        req = solr_manager.Q()
        for value in fvalues:
            if value is _marker:
                break
            req |= solr_manager.Q(**{fname: value})
        yield req


def or_queries(queries, max_size=80, solr_manager=None):
    """this will yield queries that ar a or of queries

    This permits to be sure to have queries that are not to long
    """
    # grouper iterator, see itertools recipes
    grouper = izip_longest(fillvalue=_marker, *([iter(queries)] * max_size))
    if solr_manager is None:
        solr_manager = get_solr_manager()
    for fvalues in grouper:
        req = solr_manager.Q()
        for value in fvalues:
            if value is _marker:
                break
            req |= value
        yield req


def complete_result(query, page_size=100, solr_manager=None):
    """iterate over a complete result, while using pagination in the background

    Solr results are limited in size, but using pagination permits to get
    a complete result page after page
    """
    if solr_manager is None:
        solr_manager = get_solr_manager()
    start = 0
    finished = False
    while not finished:
        current = query.paginate(start=start, rows=page_size).execute()
        for result in current:
            yield result
        start += page_size
        # a simple but robust way
        finished = len(current) < page_size


def complete_len(query, page_size=100, solr_manager=None):
    """get len of a complete result, while using pagination in the background

    Solr results are limited in size, but using pagination permits to get
    a complete result page after page
    """
    if solr_manager is None:
        solr_manager = get_solr_manager()
    start = 0
    finished = False
    cumulated = 0
    while not finished:
        current_len = len(
            query.paginate(start=start, rows=page_size).execute())
        start += page_size
        cumulated += current_len
        # a simple but robust way
        finished = current_len < page_size
    return cumulated
