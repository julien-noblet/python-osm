#!/usr/bin/python


import sys, os
import xml.dom.minidom

REL_DIR= "../"       # relation between this script and the BASE_DIR
BASE_DIR = os.path.join(os.getcwd(),
                        os.path.dirname(sys.argv[0]),
                        REL_DIR)
sys.path.append(BASE_DIR)
import pyosm



class osm_gpx_exporter(object):
    gpx_template = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <gpx xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1"
         xmlns="http://www.topografix.com/GPX/1/1"
         xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
    <metadata>
    <creator> osm_gpx_exporter </creator>
    </metadata>
    </gpx>
    """

    def __init__(self, gpx_filename):
        self.gpx_filename = gpx_filename
        self.init_gpx()

    def init_gpx(self):
        self.gpx_dom = xml.dom.minidom.parseString(self.gpx_template)
        self.gpx_root = self.gpx_dom.documentElement
    
    def append_relations(self, relations=[], recursive=True):
        """
        append an osm object to a gpx track
        relation --> track (trk)
        way --> track segment (trkseg)
        node --> track point (trkpt)
        """
        for rel in relations:
            trk = self.gpx_dom.createElement('trk')
            self.gpx_root.appendChild(trk)
            for m in rel.members:
                if type(m) != pyosm.Way:
                    continue
                trkseg = self.gpx_dom.createElement('trkseg')
                trk.appendChild(trkseg)
                for node in m.nodes:
                    trkpt = self.gpx_dom.createElement('trkpt')
                    trkpt.setAttribute('lat', node.lat)
                    trkpt.setAttribute('lon', node.lon)
                    trkseg.appendChild(trkpt)

    def write(self):
        """
        export the gpx_dom into a file
        """
        open(self.gpx_filename,'wt').write(self.gpx_dom.toprettyxml("  "))
                
                
if __name__ == '__main__':
    import getopt
    import urllib

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:r',
                                   ['outfile=', 'relations'])
    except getopt.GetoptError:
        usage()
        sys.exit()

    outfile='out.gpx'
    mode = None

    for o, a in opts:
        if o in ['-o', '--outfile']:
            outfile = a
        elif o in ['-r', 'relations']:
            mode = 'relations'

    if mode == 'relations':
        API='http://www.openstreetmap.org/api/0.6'
        gpx_exp = osm_gpx_exporter(outfile)
        
        for relid in args:
            osm = urllib.urlretrieve('%s/relation/%s/full' %(API,relid), 'temporary.osm')
            osmobj = pyosm.OSMXMLFile('temporary.osm')
            gpx_exp.append_relations(osmobj.relations)
            
        gpx_exp.write()

                       
