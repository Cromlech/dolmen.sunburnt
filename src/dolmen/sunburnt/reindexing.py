# -*- coding: utf-8 -*-
"""checking indexes and reindexing
"""
from itertools import chain

from dolmen.sunburnt.interfaces import ISolrIndexable
from dolmen.sunburnt.utilities import get_solr_manager
from dolmen.sunburnt.utils import in_queries, complete_result
from zope.cachedescriptors.property import Lazy


REINDEX = 'reindex'
ADD = 'add'
REMOVE = 'remove'

_marker = object()


class IndexRebuilder(object):
    """Rebuild index, either walking a hierarchy, either

    You shall derive your own implementation providing ``children``
    ``obj_from_dump``, ``all_query`` and ``dump_differs``
    """

    def __init__(self, commit_size=100):
        self.seen = set()  # FIXME use it to seek brains to remove
        self.commit_size = commit_size

    def children(self, obj):
        """basic containement traversal

        you may personnalize that to get all subobjects
        """
        if hasattr(obj, 'values'):
            for val in obj.values():
                yield val

    def obj_from_dump(self, dump):
        """shall return the object corresponding to a dump
        or None if no object found
        """
        raise NotImplementedError()

    def all_query(self, context):
        """query to find all existing dumps for this context"""
        return self.solr_manager.Q()

    def dump_differs(self, old, new):
        """simple implementation is to compare retrieve dump with
        computed one.

        This does not work if some fields are indexed but not stored.
        In this case you could add a digest (eg. a sha1 of the dump)
        and change this method to compare digest values
        """
        return old != new

    @Lazy
    def solr_manager(self):
        return get_solr_manager()

    @Lazy
    def unique_key(self):
        return self.solr_manager.schema.unique_key

    def rebuild_from_objects(
            self, context, dry_run=False, removal=False, always_reindex=False):
        """rebuild index starting from object context

        :param dry_run: if True does not do anything but

        :param removal: if True remove values returned by meth:unused

        :param always_reindex: if True, does not use meth:dump_differs to
            know when to replace index but always does it

        :return: yield 4 value tuples :
            object, old dump, new dump, action taken
            some value may be None
        """
        root = context
        count = 0
        manager = self.solr_manager
        commit_size = self.commit_size
        for context, dump, old, action in (
                self.walk_and_dump(context, always_reindex=always_reindex)):
            yield context, dump, old, action
            if not dry_run and (always_reindex or action is not None):
                manager.add(dump)
                count += 1
                if count > commit_size:
                    manager.commit()
        manager.commit()  # final commit

        if removal:
            unused = self.unused(root)
            if unused:
                for remove_q in in_queries(self.unique_key,
                                           unused,
                                           max_size=min(self.commit_size, 80)):
                    dumps = manager.query(remove_q).execute()
                    for dump in dumps:
                        yield self.obj_from_dump(dump), None, dump, REMOVE
                    if not dry_run:
                        manager.delete(queries=remove_q)
                        manager.commit()

    def refresh_indexed(self, query, dry_run=False):
        """Refresh indexed object index
        """
        obj_from_dump = self.obj_from_dump
        unique_key = self.unique_key
        manager = self.solr_manager
        dumps = manager.query(query).execute()
        count = 0
        for dump in dumps:
            obj = obj_from_dump(dump)
            if obj is None:
                yield obj, None, dump, REMOVE
                if not dry_run:
                    manager.delete(dump.get(unique_key))
                    count += 1
            else:
                new_dump = ISolrIndexable(obj, None)
                if self.dump_differs(dump, new_dump):
                    yield obj, new_dump, dump, REINDEX
                    if not dry_run:
                        manager.add(new_dump)
                        count += 1
                else:
                    yield obj, new_dump, dump, None
            if count > self.commit_size:
                manager.commit()
        manager.commit()

    def unused(self, context):
        manager = self.solr_manager
        res = complete_result(
            manager.query(self.all_query(context))
                .field_limit(self.unique_key), 
            solr_manager=manager)
        existing = set(r[self.unique_key] for r in res)
        return existing - self.seen

    def walk_and_dump(self, context, always_reindex=False):
        """walk context for sub-objects,
        check objects index and re-index when necessary

        self.children is a function returning an iterator
        to get an object sub items
        """
        manager = self.solr_manager
        unique_key = self.unique_key
        dump = ISolrIndexable(context, None)
        if dump is not None:
            uid = dump[unique_key]
            self.seen.add(uid)
            res = manager.query(**{unique_key: uid}).execute()
            if len(res):
                existing = res[0]
                if always_reindex or self.dump_differs(existing, dump):
                    yield context, dump, existing, REINDEX
                else:
                    yield context, dump, None, None
            else:
                # does not exists ! do add
                yield context, dump, None, ADD

        # recursively
        for res in chain(
                *[self.walk_and_dump(child, always_reindex=always_reindex)
                for child in self.children(context)]):
            yield res
