from distutils.core import setup

setup(
    name = 'python-osm', 
    version = '0.0.3',
    url = 'https://github.com/werner2101/python-osm',
    author = 'Werner Hoch',
    author_email = 'werner.ho@gmx.de',
    description = 'Provides model objects for OSM promitives and related tools',
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
