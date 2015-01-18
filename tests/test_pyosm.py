#! /usr/bin/python
import os
import sys
import unittest

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)

import pyosm

class OSMXMLFileTests(unittest.TestCase):
    def setUp(self):
        self.osm_file = open('osmfiles/multipolygon1.osm').read()
        self.osm = pyosm.OSMXMLFile(content=self.osm_file)
    
    def tearDown(self):
        pass

    def test_osm_objects(self):
        self.osm.statistic()
        r = self.osm.relations.values()[-1]
        print '\nSingle relation representation\n', r
        w = self.osm.ways.values()[-1]
        print '\nSingle way representation\n', w
        n =self.osm.nodes.values()[1]
        print '\nSingle node representation\n', n
 
        print '\nNodes of a Way:\n', w.nodes
        print '\nNodeids of a Way:\n', w.nodeids

        print '\nMember Data of a Relation:\n', r.member_data
        print '\nMembers of a Relation:\n', r.members
    
    def test_osm_itemgetter(self):
        print 'relation item test:'
        r = self.osm.relations.values()[0] # get first relation
        for it in ['id','members','member_data','tags']:
            print '  ', it, r[it]
        print 'way item test:'
        w = self.osm.ways.values()[0] # get first relation
        for it in ['id','nodes','nodeids','tags']:
            print '  ', it, w[it]
        print 'node item test:'
        n = self.osm.nodes.values()[0] # get first relation
        for it in ['id','lat', 'lon','tags']:
            print '  ', it, n[it]
    
    def test_merge_write(self):
        osm2 = pyosm.OSMXMLFile(filename='osmfiles/josm_download.osm')
        print 'osm2 stat befor merge'
        osm2.statistic()
        osm2.merge(self.osm)
        print 'osm2 stat after merge'
        osm2.statistic()
        osm2.write('testoutput/result_merge_write.osm')

if __name__ == '__main__':
    if not os.path.exists('testoutput'):
        os.mkdir('testoutput')
    unittest.main()