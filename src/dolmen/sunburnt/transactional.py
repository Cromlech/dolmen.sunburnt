"""A module to try to play nice with transactions

remind that solr is not transactionnal by itself. We try to overcome this
in a simpler but not completely safe manner.
"""
import threading
from crom import subscription, sources, target
from zope.interface import Interface, implements

try:
    import transaction
    from transaction.interfaces import IDataManager, ISynchronizer
except ImportError, e:
    if not 'transaction' in str(e):
        raise
    transaction = None
    IDataManager = ISynchronizer = Interface

from .utilities import get_solr_manager
from .interfaces import ISolrIndexable
from . import events


class DeIndexer(object):
    """Try to reindex objects indexed in transaction on transaction abort.

    You have to be able to implement these methods :
    key and object_from_doc wich give the actual object from a doc

    Both are easy if you have a constant unique key.

    Note : that this is still not really transactionnal, we just try to repair.
    this may fail in tricky concurrent cases.

    Note also that we need object_from_doc has we don't won't to reindex object
    as is in current transaction but object as it is in database, hence the
    need to retrieve original version from database.
    """
    implements(IDataManager)

    def key(self, doc):
        """unique key for a doc
        """
        raise NotImplementedError()

    def object_from_doc(self, doc):
        """retrieve object from doc

        may return None if obj no more exists
        """
        raise NotImplementedError()

    @property
    def solr_manager(self):
        return  get_solr_manager()

    def join_transaction(self):
        """Join current transaction

        implement in your subclasses"""
        raise NotImplementedError()

    def __init__(self):
        self.initialize()

    @property
    def clean(self):
       return not self.added and not self.modified

    def restore_indexes(self):
        si = self.solr_manager
        # lets undo all stuff
        for doc in self.modified.values():
            obj = self.object_from_doc(doc)
            if obj is not None:
                re_doc = ISolrIndexable(obj, None)
                if re_doc is not None:
                    si.add(re_doc)

        for doc in self.added.values():
            si.delete(doc)
        si.commit()

    def initialize(self):
        self.added = {}
        """
        docs that where added, indexed by their key
        """
        self.modified = {}
        """
        docs that where modified, indexed by their key

        removed docs are treated as modified
        """

    def register_added(self, doc):
        self.join_transaction()
        self.added[self.key(doc)] = doc

    def register_modified(self, doc):
        self.join_transaction()
        key = self.key(doc)
        if key not in self.added:  # do not to register if just added
            self.modified[key] = doc

    def register_removed(self, doc):
        self.join_transaction()
        key = self.key(doc)
        if key in self.added:
            del self.added[key]
        else:
            self.modified[key] = doc


class DeIndexerDataManager(DeIndexer):
    """Deindexer as a DataManager for transaction"""

    implements(IDataManager, ISynchronizer)

    state = None

    @property
    def transaction_manager(self):
        return transaction.manager

    def __init__(self):
        # we have to work at transaction boundaries
        self.transaction_manager.registerSynch(self)
        DeIndexer.__init__(self)

    def beforeCompletion(self, transaction):
        pass

    def newTransaction(self, transaction):
        assert self.clean

    def afterCompletion(self, transaction):
        if self.state == 'aborted':
            self.restore_indexes()
        self.initialize()
        self.state = None

    def tpc_begin(self, trans):
        self.state = 'tpc_begun'

    def commit(self, trans):
        self.state = 'commited'

    def tpc_vote(self, trans):
        pass

    def abort(self, trans):
        self.state = 'aborted'

    tpc_abort = abort

    def tpc_finish(self, trans):
        pass

    def sortKey(self):
        # please make me last as I must be aftor zodb
        return "~~~~~~~~~~~~~~"

    def join_transaction(self):
        transaction = self.transaction_manager.get()
        marker = getattr(transaction, '_dolmen_sunburnt_deindex', False)
        if not marker:
            # here we make the assumption that transaction is not shared
            # between threads 
            setattr(transaction, '_dolmen_sunburnt_deindex', True)
            # register on transaction hook
            transaction.join(self)
            assert self.clean, (
                "Inconsistent state I register to new transaction " +
                "but already got things to undo")


factory = None


def get_factory():
    return factory


def register_factory(new_factory):
    global factory
    factory = new_factory


class DeIndexerRegistry(threading.local):
    """Get current deindexer instance.

    To start using it you have to specify a deidexer manager factory
    using register_factory
    """

    current = None
    factory = None

    def get(self):
        if self.current is None or self.factory != factory:
            self.factory = factory
            self.current = self.factory()
        return self.current


registry = DeIndexerRegistry()


def get_deindexer():
    return registry.get()


@subscription
@target(Interface)
@sources(Interface, events.ISolrDumpAddedEvent)
def dump_added(ob, event):
    deindexer = get_deindexer()
    if deindexer is not None:
        deindexer.register_added(event.dump)


@subscription
@target(Interface)
@sources(Interface, events.ISolrDumpModifiedEvent)
def dump_modified(ob, event):
    deindexer = get_deindexer()
    if deindexer is not None:
        deindexer.register_modified(event.dump)


@subscription
@target(Interface)
@sources(Interface, events.ISolrDumpRemovedEvent)
def dump_removed(ob, event):
    deindexer = get_deindexer()
    if deindexer is not None:
        deindexer.register_removed(event.dump)
