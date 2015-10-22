# -*- coding: utf-8 -*-

import logging
from crom import subscription, sources, target
from dolmen.sunburnt.utilities import get_solr_manager
from dolmen.sunburnt.interfaces import ISolrIndexable
from dolmen.sunburnt.events import (
    SolrDumpAddedEvent, SolrDumpModifiedEvent, SolrDumpRemovedEvent)
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent.interfaces import (
    IObjectAddedEvent, IObjectModifiedEvent, IObjectRemovedEvent)

log = logging.getLogger('dolmen.sunburnt.processing')
log_debug = log.isEnabledFor(logging.DEBUG)


@subscription
@target(Interface)
@sources(Interface, IObjectAddedEvent)
def indexDocSubscribe(ob, event):
    dump = ISolrIndexable(event.object, None)
    if dump is not None:
        manager = get_solr_manager()
        manager.add(dump)
        notify(SolrDumpAddedEvent(ob, dump))
        log_debug and log.debug('Added dump : %s' % dump)
        manager.commit()


@subscription
@target(Interface)
@sources(Interface, IObjectModifiedEvent)
def reindexDocSubscribe(ob, event):
    dump = ISolrIndexable(event.object, None)
    if dump is not None:
        manager = get_solr_manager()
        manager.add(dump)
        notify(SolrDumpModifiedEvent(ob, dump))
        log_debug and log.debug('Updated dump : %s' % dump)
        manager.commit()


@subscription
@target(Interface)
@sources(Interface, IObjectRemovedEvent)
def unindexDocSubscribe(ob, event):
    dump = ISolrIndexable(event.object, None)
    if dump is not None:
        manager = get_solr_manager()
        manager.delete(dump)
        notify(SolrDumpRemovedEvent(ob, dump))
        log_debug and log.debug('Removed dump : %s' % dump)
        manager.commit()
