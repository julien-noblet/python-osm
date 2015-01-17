#! /usr/bin/python
import os
import sys
import unittest

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)

import pyosm
import osmdb


class OsmDbTests(unittest.TestCase):
    def setUp(self):
        # local uncompressed file of the planet file
        print 'load planet'
        self.db = osmdb.OsmDb('/store/osm/planet-latest.osm')
    
    def tearDown(self):
        pass

    def test_get_objects(self):
    #db = osmdb.Bz2OsmDb('/store/osm/files/australia.osm.bz2')
    #db = osmdb.OsmDb('/store/osm/files/australia.osm')
    
        print 'Node: small id'
        ret = self.db.get_objects('node',[1])
        print '  return length', len(ret)
        
        print 'Node: regular ids'
        ret = self.db.get_objects('node',[579259,579260])
        print '  return length', len(ret)
        
        print 'Node: large ids'
        ret = self.db.get_objects('node',[12345678900])
        print '  return length', len(ret)
        
        print 'Way: small id'
        ret = self.db.get_objects('way',[1])
        print '  return length', len(ret)
        
        print 'Way: regular ids'
        ret = self.db.get_objects('way',[174372276,168734042])
        print '  return length', len(ret)
        
        print 'Way: large ids'
        ret = self.db.get_objects('way',[12345678900])
        print '  return length', len(ret)
        
        print 'Relation: small id'
        ret = self.db.get_objects('relation',[1])
        print '  return length', len(ret)
        
        print 'Relation: regular ids'
        ret = self.db.get_objects('relation',[6188])
        print '  return length', len(ret)
        
        print 'Relation: large ids'
        ret = self.db.get_objects('relation',[12345678900])
        print '  return length', len(ret)
        
        print 'Relation: regular id, recursive call'
        ret = self.db.get_objects_recursive('relation',[6188], True)
        print '  return length', len(ret)        


class Bz2OsmDbTests(unittest.TestCase):
    def setUp(self):
        # local bz2 compressed file of australia file
        print 'load australia'
        self.db = osmdb.Bz2OsmDb('/store/osm/files/australia.osm.bz2')
    
    def tearDown(self):
        pass

    def test_get_objects(self):
        print 'Node: small id'
        ret = self.db.get_objects('node',[1])
        print '  return length', len(ret)
        
        print 'Node: regular ids'
        ret = self.db.get_objects('node',[579259,579260])
        print '  return length', len(ret)
        
        print 'Node: large ids'
        ret = self.db.get_objects('node',[12345678900])
        print '  return length', len(ret)
        
        print 'Way: small id'
        ret = self.db.get_objects('way',[1])
        print '  return length', len(ret)
        
        print 'Way: regular ids'
        ret = self.db.get_objects('way',[174372276,168734042])
        print '  return length', len(ret)
        
        print 'Way: large ids'
        ret = self.db.get_objects('way',[12345678900])
        print '  return length', len(ret)
        
        print 'Relation: small id'
        ret = self.db.get_objects('relation',[1])
        print '  return length', len(ret)
        
        print 'Relation: regular ids'
        ret = self.db.get_objects('relation',[6188])
        print '  return length', len(ret)
        
        print 'Relation: large ids'
        ret = self.db.get_objects('relation',[12345678900])
        print '  return length', len(ret)
        
        print 'Relation: regular id, recursive call'
        ret = self.db.get_objects_recursive('relation',[6188], True)
        print '  return length', len(ret)  

if __name__ == '__main__':
    unittest.main()        
        