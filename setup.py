# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


version = '0.1'

test_require = [
    'pytest',
    'transaction',
    ]

setup(name='dolmen.sunburnt',
      version=version,
      description="SolR Indexer for Cromlech",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['dolmen'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'crom',
          'setuptools',
          'sunburnt >= 0.5',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.lifecycleevent',
          'zope.schema',
          'httplib2', # required by sunburnt
      ],
      extras_require = {'test': test_require},
      entry_points="""
      # -*- Entry points: -*-
      [paste.filter_app_factory]
      solr = dolmen.sunburnt.wsgi:SolrFactory
      """,
      )
