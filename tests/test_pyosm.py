#!/usr/bin/python
import sys, os

PYOSM_DIR = os.path.join(os.path.dirname(__file__), '../src/osm/')
sys.path.append(PYOSM_DIR)

import pyosm
import multipolygon


osm = pyosm.OSMXMLFile('xx.osm')
osm2 = pyosm.OSMXMLFile('../../../Grenzen/Bodenseekreis.osm')
osm.statistic()


r = osm.relations.values()[6]
print '\nSingle relation representation\n', r
w = osm.ways.values()[-1]
print '\nSingle way representation\n', w
n =osm.nodes.values()[1]
print '\n', n

print '\nNodes of a Way:\n', w.nodes
print '\nNodeids of a Way:\n', w.nodeids

print '\nMember Data of a Relation:\n', r.member_data
print '\nMembers of a Relation:\n', r.members

print '\nmerge 2 osm files and print statistic:'
osm.merge(osm2)
osm.statistic()
osm.write('xx_writetest.osm')

print '\nMultipolygon class test'
mp = multipolygon.multipolygon(osm.relations[62635])
mp.status()
                               
