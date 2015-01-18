#! /usr/bin/python
import os
import sys
import unittest
import logging

srcDir = os.path.abspath('../src/osm')
sys.path.insert(1, srcDir)

import osmdb
log = logging.getLogger(__name__)

class OsmDbTests(unittest.TestCase):
    def setUp(self):
        # local uncompressed file of the planet file
        log.info('load planet')
        self.db = osmdb.OsmDb('/store/osm/planet-latest.osm')
    
    def tearDown(self):
        pass

    def test_get_objects(self):
    #db = osmdb.Bz2OsmDb('/store/osm/files/australia.osm.bz2')
    #db = osmdb.OsmDb('/store/osm/files/australia.osm')
    
        log.info('Node: small id')
        ret = self.db.get_objects('node',[1])
        log.info('  return length', len(ret))
        
        log.info('Node: regular ids')
        ret = self.db.get_objects('node',[579259,579260])
        log.info('  return length', len(ret))
        
        log.info('Node: large ids')
        ret = self.db.get_objects('node',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Way: small id')
        ret = self.db.get_objects('way',[1])
        log.info('  return length', len(ret))
        
        log.info('Way: regular ids')
        ret = self.db.get_objects('way',[174372276,168734042])
        log.info('  return length', len(ret))
        
        log.info('Way: large ids')
        ret = self.db.get_objects('way',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Relation: small id')
        ret = self.db.get_objects('relation',[1])
        log.info('  return length', len(ret))
        
        log.info('Relation: regular ids')
        ret = self.db.get_objects('relation',[6188])
        log.info('  return length', len(ret))
        
        log.info('Relation: large ids')
        ret = self.db.get_objects('relation',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Relation: regular id, recursive call')
        ret = self.db.get_objects_recursive('relation',[6188], True)
        log.info('  return length', len(ret))    


class Bz2OsmDbTests(unittest.TestCase):
    def setUp(self):
        # local bz2 compressed file of australia file
        log.info('load australia')
        self.db = osmdb.Bz2OsmDb('/store/osm/files/australia.osm.bz2')
    
    def tearDown(self):
        pass

    def test_get_objects(self):
        log.info('Node: small id')
        ret = self.db.get_objects('node',[1])
        log.info('  return length', len(ret))
        
        log.info('Node: regular ids')
        ret = self.db.get_objects('node',[579259,579260])
        log.info('  return length', len(ret))
        
        log.info('Node: large ids')
        ret = self.db.get_objects('node',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Way: small id')
        ret = self.db.get_objects('way',[1])
        log.info('  return length', len(ret))
        
        log.info('Way: regular ids')
        ret = self.db.get_objects('way',[174372276,168734042])
        log.info('  return length', len(ret))
        
        log.info('Way: large ids')
        ret = self.db.get_objects('way',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Relation: small id')
        ret = self.db.get_objects('relation',[1])
        log.info('  return length', len(ret))
        
        log.info('Relation: regular ids')
        ret = self.db.get_objects('relation',[6188])
        log.info('  return length', len(ret))
        
        log.info('Relation: large ids')
        ret = self.db.get_objects('relation',[12345678900])
        log.info('  return length', len(ret))
        
        log.info('Relation: regular id, recursive call')
        ret = self.db.get_objects_recursive('relation',[6188], True)
        log.info('  return length', len(ret))

if __name__ == '__main__':
    unittest.main()        
        