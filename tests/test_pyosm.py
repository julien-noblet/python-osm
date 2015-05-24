#! /usr/bin/python
import os
import sys
import unittest
import logging
import numpy

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)
from src.osm import pyosm

log = logging.getLogger(__name__)

class OSMXMLFileTests(unittest.TestCase):
    def setUp(self):
        self.osm_file = 'file://'+os.getcwd()+'/tests/osmfiles/multipolygon1.osm'
        self.osm = pyosm.OSMXMLFile(self.osm_file)

    def tearDown(self):
        pass

    def test_osm_objects(self):
        self.osm.statistic()
        r = list(self.osm.relations.values())[-1]
        log.info('Single relation representation: %s', r)
        w = list(self.osm.ways.values())[-1]
        log.info('\nSingle way representation: %s', w)
        n = list(self.osm.nodes.values())[1]
        log.info('Single node representation: %s', n)

        log.info('Nodes of a Way: %s', w.nodes)
        log.info('Nodeids of a Way: %s', w.nodeids)

        log.info('Member Data of a Relation: %s', r.member_data)
        log.info('Members of a Relation: %s', r.members)

    def test_osm_itemgetter(self):
        log.info('relation item test:')
        r = list(self.osm.relations.values())[0] # get first relation
        for it in ['id','members','member_data','tags']:
            log.info('  %s=%s', it, r[it])
        log.info('way item test:')
        w = list(self.osm.ways.values())[0] # get first relation
        for it in ['id','nodes','nodeids','tags']:
            log.info('  %s=%s', it, w[it])
        log.info('node item test:')
        n = list(self.osm.nodes.values())[0] # get first relation
        for it in ['id','lat', 'lon','tags']:
            log.info('  %s=%s', it, n[it])

    def test_merge_write(self):
        osm2 = pyosm.OSMXMLFile(filename='file://'+os.getcwd()+'/tests/osmfiles/josm_download.osm')
        log.info('osm2 stat befor merge')
        osm2.statistic()
        osm2.merge(self.osm)
        log.info('osm2 stat after merge')
        osm2.statistic()

        osm2.write(os.path.join(os.getcwd(),'tests/osmfiles/result_merge_write.osm'))

if __name__ == '__main__':
    if not os.path.exists('testoutput'):
        os.mkdir('testoutput')
    logging.basicConfig(level=logging.INFO)
    unittest.main()
