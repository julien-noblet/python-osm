#!/usr/bin/python


import sys
import xml.dom.minidom

sys.path.append('../')
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
    
    def append_osm(self, osm, relation=None, way=None, node=None):
        """
        append an osm object to a gpx track
        relation --> track (trk)
        way --> track segment (trkseg)
        node --> track point (trkpt)
        """
        if relation != None:
            pass
        elif way != None:
            pass
        elif node != None:
            pass
        else:
            ways = osm.ways
        
        trk = self.gpx_dom.createElement('trk')
        self.gpx_root.appendChild(trk)
        for way in ways:
            trkseg = self.gpx_dom.createElement('trkseg')
            trk.appendChild(trkseg)
            for node in way.nodes:
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
    osm = pyosm.OSMXMLFile('relation157307.osm')
    osm.statistic()
    gpx_exp = osm_gpx_exporter('out.gpx')
    gpx_exp.append_osm(osm)
    gpx_exp.write()

                       
