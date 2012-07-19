#!/usr/bin/python
import sys, os
import re, math
import urllib
import httplib

PYOSM_DIR = os.path.join(os.path.dirname(__file__), '../src')
sys.path.append(PYOSM_DIR)
from osm import pyosm

VERSION = "0.0.2"

#################### CONSTANTS
URL='www.openstreetmap.org'
API='/api/0.6'

#################### FUNCTIONS
def elementhistory(date, relations, ways, nodes):
    osmhist = pyosm.OSMXMLFile()

    ## working stacks for all object types
    relation_stack = set([int(r) for r in relations])
    way_stack = set([int(w) for w in ways])
    node_stack = set([int(n) for n in nodes])

    ## load recursively all missing relations
    while relation_stack:
        relid = relation_stack.pop()
        rel = bisect('relation', relid, date)
        osmhist.merge(rel)
        for mtype, mid, mrole in rel.relations[relid].member_data:
            if mtype == 'r':
                if mid not in osmhist.relations:
                    relation_stack.add(mid)
            elif mtype == 'w':
                way_stack.add(mid)
            elif mtype == 'n':
                node_stack.add(mid)
            else:
                raise ValueError('Unknown member type: "%r"' % mtype)
    
    ## load all ways
    for wayid in way_stack:
        way = bisect('way', wayid, date)
        osmhist.merge(way)
        node_stack.update(way.ways[wayid].nodeids)

    ## load all nodes
    for nodeid in node_stack:
        node = bisect('node', nodeid, date)
        osmhist.merge(node)

    return osmhist


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
    content=ans.read()
    curr_osm = pyosm.OSMXMLFile(content=content)
    curr_obj = getobject(curr_osm, objtype, objid)
    newest_version = int(curr_obj.version)

    if curr_obj.timestamp < date:
        return curr_osm

    bysect_version = 2**int(math.log(int(curr_obj.version)-1,2))
    bysect_step = bysect_version
    
    while bysect_step:
        url = '%s/%s/%d/%d' %(API, objtype, objid, bysect_version)
        log(' bisect:', url)
        conn.request('GET', url)
        ans = conn.getresponse()
        bysect_osm = pyosm.OSMXMLFile(content=ans.read())
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

    if newest_version > int(curr_obj.version):
        curr_obj.tags['osmhistory:old_version_date'] = str(int(curr_obj.version)) + '_' + date
    curr_obj.set_attr('version', str(newest_version))
    
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


def usage():
    print sys.argv[0] + " Version " + VERSION
    print "  -h, --help: print this help information"
    print "  -t, --timestamp: date for the history. format: YYYY-MM-DD"
    print "  -o, --outfile: filename for the output filename"
    print "  -n, --nodes: comma separated list of node ids"
    print "  -w, --ways: comma separated list of way ids"
    print "  -r, --relations: comma separated list of relation ids"
    print "Examples:"
    print "  osmhistory.py -t 2009-10-01 -w 13415127,26802382 -o foo.osm"
    print "  osmhistory.py -t 2009-10-01 --relations=21328 -o rel_21628.osm"
    sys.exit()

#################### MAIN
if __name__ == '__main__':
    import getopt
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ht:o:r:w:n:',
                                   ['help', 'timestamp=', 'outfile=', 'relations=', 'ways=', 'nodes='])
    except getopt.GetoptError:
        usage()

    ## default values
    outfile = 'out.osm'
    nodes = []
    ways = []
    relations = []

    for o, a in opts:
        if o in ['-h', '--help']:
            usage()
        elif o in ['-t', '--timestamp']:
            if re.match('20[0-9]{2}-[0-9]{2}-[0-9]{2}$', a):
                date = a
            else:
                print 'Error: invalid date'
                usage()
        elif o in ['-o', '--outfile']:
            outfile = a
        elif o in ['-n', '--nodes']:
            if re.match('[1-9][0-9\,]*[0-9]$', a):
                nodes = a.split(',')
            else:
                print 'Error: invalid nodes list'
                usage()
        elif o in ['-w', '--ways']:
            if re.match('[1-9][0-9,]*[0-9]$', a):
                ways = a.split(',')
            else:
                print 'Error: invalid ways list'
                usage()
        elif o in ['-r', '--relations']:
            if re.match('[1-9][0-9,]*[0-9]$', a):
                relations = a.split(',')
            else:
                print 'Error: invalid relations list'
                usage()

    osm = elementhistory(date, relations, ways, nodes)
    osm.write(outfile)



