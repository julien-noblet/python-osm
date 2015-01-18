#! /usr/bin/python
import os
import sys
import unittest
import logging

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)
import pyosm

log = logging.getLogger(__name__)

class OSMXMLFileTests(unittest.TestCase):
    def setUp(self):
        self.osm_file = 'osmfiles/multipolygon1.osm'
        self.osm = pyosm.OSMXMLFile(self.osm_file)
    
    def tearDown(self):
        pass

    def test_osm_objects(self):
        self.osm.statistic()
        r = list(self.osm.relations.values())[-1]
        log.info('\nSingle relation representation\n', r)
        w = list(self.osm.ways.values())[-1]
        log.info('\nSingle way representation\n', w)
        n = list(self.osm.nodes.values())[1]
        log.info('\nSingle node representation\n', n)
 
        log.info('\nNodes of a Way:\n', w.nodes)
        log.info('\nNodeids of a Way:\n', w.nodeids)

        log.info('\nMember Data of a Relation:\n', r.member_data)
        log.info('\nMembers of a Relation:\n', r.members)
    
    def test_osm_itemgetter(self):
        log.info('relation item test:')
        r = list(self.osm.relations.values())[0] # get first relation
        for it in ['id','members','member_data','tags']:
            log.info('  ', it, r[it])
        log.info('way item test:')
        w = list(self.osm.ways.values())[0] # get first relation
        for it in ['id','nodes','nodeids','tags']:
            log.info('  ', it, w[it])
        log.info('node item test:')
        n = list(self.osm.nodes.values())[0] # get first relation
        for it in ['id','lat', 'lon','tags']:
            log.info('  ', it, n[it])
    
    def test_merge_write(self):
        osm2 = pyosm.OSMXMLFile(filename='osmfiles/josm_download.osm')
        log.info('osm2 stat befor merge')
        osm2.statistic()
        osm2.merge(self.osm)
        log.info('osm2 stat after merge')
        osm2.statistic()
        osm2.write('testoutput/result_merge_write.osm')

if __name__ == '__main__':
    if not os.path.exists('testoutput'):
        os.mkdir('testoutput')
    unittest.main()