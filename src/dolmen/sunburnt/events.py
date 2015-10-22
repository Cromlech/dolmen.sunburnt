# -*- coding: utf-8 -*-

from zope.interface.interfaces import IObjectEvent, ObjectEvent
from zope.interface import Attribute, implements


class ISolrDumpEvent(IObjectEvent):
    """Base event for dump"""

    dump = Attribute("Solr dump")


class ISolrDumpAddedEvent(ISolrDumpEvent):
    """New dump added"""


class ISolrDumpModifiedEvent(ISolrDumpEvent):
    """New dump modified"""


class ISolrDumpRemovedEvent(ISolrDumpEvent):
    """New dump removed"""


class SolrDumpEvent(ObjectEvent):
    """Base solr dump event implementation"""
    implements(ISolrDumpEvent)

    def __init__(self, obj, dump):
        super(SolrDumpEvent, self).__init__(obj)
        self.dump = dump


class SolrDumpAddedEvent(SolrDumpEvent):
    implements(ISolrDumpAddedEvent)


class SolrDumpModifiedEvent(SolrDumpEvent):
    implements(ISolrDumpModifiedEvent)


class SolrDumpRemovedEvent(SolrDumpEvent):
    implements(ISolrDumpRemovedEvent)
