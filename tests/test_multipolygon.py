#! /usr/bin/python
import os
import sys
import unittest

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)

from src.osm import pyosm
from src.osm import multipolygon


class OSMXMLFileTests(unittest.TestCase):
    def setUp(self):
        self.osm_file = os.path.join(os.getcwd(),'tests/','osmfiles/multipolygon1.osm')
        self.osm = pyosm.OSMXMLFile(self.osm_file)

    def tearDown(self):
        pass

    def test_multipolygon(self):
        mp = multipolygon.multipolygon(self.osm.relations[179755])
        mp.status()

    def test_josmfile(self):
        mp = multipolygon.multipolygon(self.osm.relations[179755])
        mp.write_josm_file(os.path.join(os.getcwd(),'tests/','testoutput/josmfile.xml'))

    def test_osmosisfile(self):
        mp = multipolygon.multipolygon(self.osm.relations[179755])
        mp.write_osmosis_file(os.path.join(os.getcwd(),'tests/','testoutput/josmfile.xml'))

    def test_point_in_polygon(self):
        mp = multipolygon.multipolygon(self.osm.relations[179755])
        points = [(9.58533328102,47.66978302865),
                  (9.58518367709,47.66978913432),
                  (9.58497428566,47.66984484554),
                  (9.58481320699,47.66985426283),
                  (9.58466333116,47.66985520476),
                  (9.58451372723,47.66986131043)]
        inside = mp.inside(points=points)
        self.assertAlmostEqual(inside.sum(), 4)


if __name__ == '__main__':
    if not os.path.exists('testoutput'):
        os.mkdir('testoutput')
    unittest.main()
