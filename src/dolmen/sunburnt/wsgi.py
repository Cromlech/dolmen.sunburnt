# -*- coding: utf-8 -*-

from dolmen.sunburnt.utilities import local_solr, basic_conf


class Configuration(dict):

    def __init__(self, base_attrs):
        self.update(base_attrs)

    def update(self, attrs):
        dict.update(self, attrs)
        self.__dict__.update(attrs)


class SolrWrapper(object):

    key = 'solr.sunburnt.config'

    def __init__(self, config, app):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        local_solr.config = self.config
        environ[self.key] = self.config
        return self.app(environ, start_response)


def SolrFactory(app, global_conf, **local_conf):
    """Factory for the SolR connector.
    """
    config = Configuration(basic_conf)
    config.update(local_conf)
    return SolrWrapper(config, app)
