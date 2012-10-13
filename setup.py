#!/usr/bin/python
from distutils.core import setup

setup(
    name = "python-osm", 
    version = "0.0.2",
    description = "OpenStreetMap library for python ",
    scripts = [
             'tools/osmhistory.py', 
             'tools/relation2gpx.py'
    ], 
    py_modules = ['osm.pyosm',
                  'osm.multipolygon',
                  'osm.osmdb',
                  'osm.utils'
                  ],
    package_dir = {'osm': 'src/osm'},
)

