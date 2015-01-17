#! /usr/bin/python
import os
import sys
import unittest

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)

import pyosm
import multipolygon


class OSMXMLFileTests(unittest.TestCase):
    def setUp(self):
        self.osm_file = open('osmfiles/multipolygon1.osm').read()
        self.osm = pyosm.OSMXMLFile(content=self.osm_file)
    
    def tearDown(self):
        pass

    def test_multipolygon(self):
        mp = multipolygon.multipolygon(self.osm.relations[179755])
        mp.status()
        
if __name__ == '__main__':
    if not os.path.exists('testoutput'):
        os.mkdir('testoutput')
    unittest.main()        
        