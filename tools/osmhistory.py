#!/usr/bin/python
import sys, os
import math
import urllib
import httplib

PYOSM_DIR = os.path.join(os.path.dirname(__file__), '../src')
sys.path.append(PYOSM_DIR)
import pyosm

#################### CONSTANTS
URL='www.openstreetmap.org'
API='/api/0.6'

#################### FUNCTIONS
def elementhistory(objtype, objid, date):
    if objtype not in ['way', 'relation']:
        print 'Objecttype "%s" not supportet' % objtype
        return

    osmhist = bisect(objtype, objid, date)
    
    for way in osmhist.ways.values():
        if type(way) == pyosm.ObjectPlaceHolder:
            osmway = bisect('way', way.id, date)
            osmhist.merge(osmway)

    for node in osmhist.nodes.values():
        if type(node) == pyosm.ObjectPlaceHolder:
            osmnode = bisect('node', node.id, date)
            osmhist.merge(osmnode)
    
    osmhist.write('%s_%s_%s.osm' %(objtype, objid, date))


def bisect(objtype, objid, date, maxversion=None ):
    conn = httplib.HTTPConnection(URL)
    osmobj = None
    minversion = 1
    log('bisect:' + objtype, objid)
    if not maxversion:
        url = '%s/%ss?%ss=%d' %(API, objtype, objtype, objid)
    else:
        url = '%s/%s/%d/%d' %(API, objtype, objid, maxversion)

    log(' bisect:', url)

    conn.request('GET', url)
    ans = conn.getresponse()
    open('xx.osm', 'wt').write(ans.read())
    curr_osm = pyosm.OSMXMLFile('xx.osm')
    curr_obj = getobject(curr_osm, objtype, objid)
    newest_version = curr_obj.version

    if curr_obj.timestamp < date:
        return curr_osm

    bysect_version = 2**int(math.log(curr_obj.version-1,2))
    bysect_step = bysect_version
    
    while bysect_step:
        url = '%s/%s/%d/%d' %(API, objtype, objid, bysect_version)
        log(' bisect:', url)
        conn.request('GET', url)
        ans = conn.getresponse()
        open('xx.osm', 'wt').write(ans.read())
        bysect_osm = pyosm.OSMXMLFile('xx.osm')
        bysect_obj = getobject(bysect_osm, objtype, objid)

        bysect_step = int(bysect_step / 2)
        if bysect_obj.timestamp < date:
            curr_osm = bysect_osm
            curr_obj = bysect_obj
            bysect_version += bysect_step
            while bysect_version >= newest_version and bysect_step:
                bysect_step = int(bysect_step / 2)
                bysect_version -= bysect_step
        else:
            bysect_version -= bysect_step

    curr_obj.tags['myold_version'] = str(curr_obj.version)
    curr_obj.version = newest_version
    
    conn.close()
    return curr_osm

def getobject(osmobj, objtype, objid):
    if objtype == 'node':
        obj = osmobj.nodes[objid]
    elif objtype == 'way':
        obj = osmobj.ways[objid]
    elif objtype == 'relation':
        obj = osmobj.relations[objid]
    else:
        raise ValueError

    return obj

def log(s, ss=''):
    if True:
        sys.stdout.write(str(s) + str(ss) + '\n')

#################### MAIN
## vorhandenes objekt
#o = bisect('way', 13415127, '2009-10-28')
#o.write('xx1.osm')

## maxversion object
#o = bisect('way', 26802382, '2009-04-01')
#o.write('xx2.osm')




#elementhistory('way', 26802382, '2009-11-28')
#elementhistory('way', 17788500, '2009-06-29')
elementhistory('relation', 21628, '2009-10-01')






