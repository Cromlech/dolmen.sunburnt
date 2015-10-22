# -*- coding: utf-8 -*-

from zope.interface import Interface, Attribute
from zope.schema import Bool, TextLine, Int
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('dolmen.sunburnt')


class ISolrSchema(Interface):

    active = Bool(
        default=False,
        title=_(u'Active'),
        description=_(u'Check this to enable the Solr integration, i.e. '
                      u'indexing and searching using the below settings.'))

    host = TextLine(
        title=_(u'Host'),
        description=_(u'The host name of the Solr instance to be used.'))

    port = Int(
        title=_(u'Port'),
        description=_(u'The port of the Solr instance to be used.'))

    auto_commit = Bool(
        default=True,
        title=_(u'Automatic commit'),
        description=_(u'If enabled each index operation will cause a commit '
                      u'to be sent to Solr, which causes it to update its '
                      u'index. If you disable this, you need to configure '
                      u'commit policies on the Solr server side.'))

    commit_within = Int(
        default=0,
        title=_(u'Commit within'),
        description=_(u'Maximum number of milliseconds after which adds '
                      u'should be processed by Solr. Defaults to 0, meaning '
                      u'immediate commits. Enabling this feature implicitly '
                      u'disables automatic commit and you should configure '
                      u'commit policies on the Solr server side. Otherwise '
                      u'large numbers of deletes without adds will not be '
                      u'processed. This feature requires a Solr 1.4 server.'))


class ISolrManager(Interface):
    """A connection manager.
    """
    manager = Attribute('Sunburnt SolR interface')


class IIndexable(Interface):
    pass


class ISolrIndexable(Interface):
    pass
