# -*- coding: utf-8 -*-

import threading
from logging import getLogger
from sunburnt import SolrInterface

logger = getLogger('dolmen.sunburnt.manager')
marker = object()


basic_conf = {
    'protocol': 'http',
    'base': '/solr',
    'host': None,
    'port': None,
    'async': True,
    'auto_commit': False,
    'commit_within': 0,
    }


class LocalSolR(threading.local):
    """SolR local information.
    """
    config = None
    manager = None


local_solr = LocalSolR()


def solr_manager(config):
    manager = local_solr.manager
    if manager is None:
        url = "%s://%s:%s%s" % (
            config.protocol,
            config.host,
            config.port,
            config.base)
        manager = SolrInterface(url)
        logger.info("Connexion created to %s." % url)
        local_solr.manager = manager
    return manager


def get_solr_manager():
    config = local_solr.config
    if config is None:
        logger.error("Configuration doesn't exist. Aborting connexion.")
        raise ValueError("Can't create SolR manager without configuration")
    return solr_manager(local_solr.config)
