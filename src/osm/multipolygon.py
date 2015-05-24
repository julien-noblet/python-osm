#!/usr/bin/python

import sys
from src.osm import pyosm
from src.osm.utils import deg2num, num2deg
import numpy

try:
    #nxutils is only used in older matplotlib version (<1.2.x)
    import matplotlib.nxutils
    HAS_NXUTILS = True
except:
    HAS_NXUTILS = False
    import matplotlib.path


class multipolygon(object):

    def __init__(self, relation):
        self.relation = relation
        self.read_relation(self.relation)

    def read_relation(self, relation):
        """
        read the relation and prepare the multipolygon object.
        """
        members = self.recursive_members(relation)

        inner_ways = []
        outer_ways = []
        for obj,role in members:
            if type(obj) == pyosm.Way:
                if role in ['outer', '']:
                    outer_ways.append(obj)
                elif role in ['inner']:
                    inner_ways.append(obj)
                else:
                    sys.stderr.write('Unknown role "%s" of way %i\n' % (role, obj.id))
            elif type(obj) == pyosm.Node:
                sys.stderr.write('Node obj in role "%s" of node %i\n' % (role, obj.id))

        self.inner_polygons, self.inner_ways = self.create_polygons(inner_ways)
        self.outer_polygons, self.outer_ways = self.create_polygons(outer_ways)


    def create_polygons(self, ways):
        """
        sort the osm ways to inner and outer polygon way list.
        Connect all osm ways that belongs together into single polygon ways.
        """
        ways = ways + []    ## list copy
        polygons = []
        open_ways = []

        endnodes = {}
        for w in ways:
            start = w.nodes[0]
            stop = w.nodes[-1]
            if start.id == stop.id:
                ## a closed way is a polygon
                polygons.append(w.nodes)
                continue
            if start.id in endnodes:
                endnodes[start.id].append(w)
            else:
                endnodes[start.id] = [w]
            if stop.id in endnodes:
                endnodes[stop.id].append(w)
            else:
                endnodes[stop.id] = [w]

        poly_nodes = []

        while endnodes:
            way = iter(endnodes.values()).__next__()[0]
            startway = way
            endway = way
            poly_nodes.extend(way.nodes)
            while True:
                startnode = poly_nodes[0]
                stopnode = poly_nodes[-1]
                if startnode == stopnode:
                    endnodes.pop(startnode.id)
                    polygons.append(poly_nodes)
                    poly_nodes = []
                    break

                if startway:
                    ways = endnodes.pop(startnode.id)
                    if len(ways) == 1:
                        sys.stderr.write('open node %s of way %s\n' % (startnode.id, ways[0].id))
                        startway = None
                        continue
                    elif len(ways) == 2:
                        if ways[0] == startway:
                            appendway = ways[1]
                        else:
                            appendway = ways[0]
                        if appendway.nodes[-1] == startnode:
                            poly_nodes = appendway.nodes + poly_nodes
                        else:
                            poly_nodes = appendway.nodes[::-1] + poly_nodes
                        startway = appendway
                        continue
                    else:
                        sys.stderr.write('node with more than 2 ways %s\n' % (startnode.id))

                if endway:
                    ways = endnodes.pop(stopnode.id)
                    if len(ways) == 1:
                        sys.stderr.write('open node %s of way %s\n' % (stopnode.id, ways[0].id))
                        endway = None
                        continue
                    elif len(ways) == 2:
                        if ways[0] == endway:
                            appendway = ways[1]
                        else:
                            appendway = ways[0]
                        if appendway.nodes[0] == stopnode:
                            poly_nodes = poly_nodes + appendway.nodes
                        else:
                            poly_nodes = poly_nodes + appendway.nodes[::-1]
                        endway = appendway
                        continue
                    else:
                        sys.stderr.write('node with more than 2 ways %s\n' % (stopnode.id))

                ## no way found to append
                open_ways.append(poly_nodes)
                poly_nodes = []
                break

        return polygons, open_ways


    def recursive_members(self, relation):
        """
        collect recursively all way/node members of a hierarchical multipolygon relation.
        returns a list of (obj,role) tuples of all member elements.
        """
        todo_stack = [relation]
        members = []
        recursive_relations = set()

        while todo_stack:
            current_relation = todo_stack.pop(0)

            if current_relation in recursive_relations:
                raise Exception('recursion loops in relation %i' % self.relation.id)
            recursive_relations.add(current_relation)

            for m in current_relation.members:
                obj, role = m
                if type(obj) == pyosm.Relation and role in ['inner','outer','']:
                    todo_stack.append(obj)
                elif role in ['inner','outer','']:
                    members.append(m)
                else: # drop all bad members like subarea, admin_centre
                    pass

        return members

    def inside(self, nodes=[], points=[]):
        """
        check if the nodes from the nodes list are inside the multipolygon
        """
        if nodes:
            points = self.pointlist(nodes)
        matches = numpy.zeros(len(points))
        for outerpoly in self.outer_polygons:
            outerpoints = self.pointlist(outerpoly)
            if HAS_NXUTILS:
                matches = matches + matplotlib.nxutils.points_inside_poly(points, outerpoints)
            else:
                matches = matches + matplotlib.path.Path(outerpoints).contains_points(points)
        for innerpoly in self.inner_polygons:
            innerpoints = self.pointlist(innerpoly)
            if HAS_NXUTILS:
                matches = matches - matplotlib.nxutils.points_inside_poly(points, innerpoints)
            else:
                matches = matches - matplotlib.path.Path(innerpoints).contains_points(points)
        return matches

    def pointlist(self, nodes):
        """
        returns a list of (lon/lat) points of a given node list
        """
        points = []
        for node in nodes:
            points.append((float(node.lon), float(node.lat)))
        return points

    def write_osmosis_file(self, filename):
        """
        create a boundary polygon for osmosis
        """
        fid = open(filename, 'wt')
        n = 1
        fid.write('xxx\n')
        for op in self.outer_polygons:
            fid.write('%i\n' %(n))
            for node in op:
                fid.write('\t%s\t%s\n' %(node.lon, node.lat))
            fid.write('END\n')
            n += 1

        for ip in self.inner_polygons:
            fid.write('xxx\n')
            fid.write('!%i\n' %(n))
            for node in ip:
                fid.write('\t%f\t%f\n' %(node.lat, node.lon))
            fid.write('END\n')
            n += 1
        fid.write('END\n')
        fid.close()

    def write_josm_file(self, filename, tilezoom=14):
        """
        create a osm file for the editor JOSM, that only contains the download boundary
        information.
        Load the file in JOSM and update the data.
        Note: Please do not missuse this function to download large areas with josm
        """
        from shapely.geometry import LineString, Polygon

        f_out = open(filename,'w')
        f_out.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        f_out.write("<osm version='0.6' upload='true' generator='JOSM'>\n")

        for i, op in enumerate(self.outer_polygons):
            # create coordinate list and then a polygon
            plist = [(node.lat, node.lon) for node in op]
            outer_polygon = Polygon(LineString(plist))

            if not outer_polygon.is_valid:
                raise ValueError('outer polygon no %i is not valid' % (i+1))

            (minlat, minlon, maxlat, maxlon) = outer_polygon.bounds
            (x1, y2) = deg2num(minlat, minlon, tilezoom)
            (x2, y1) = deg2num(maxlat, maxlon, tilezoom)

            for ty in range(y1, y2 + 1):
                for tx in range(x1, x2 + 1):
                    tile_rectangle = [num2deg(tx, ty, tilezoom),
                                      num2deg(tx+1, ty, tilezoom),
                                      num2deg(tx+1, ty+1, tilezoom),
                                      num2deg(tx, ty+1, tilezoom),
                                      num2deg(tx, ty, tilezoom)]
                    tile_polygon = Polygon(tile_rectangle)

                    if outer_polygon.contains(tile_polygon) or outer_polygon.intersects(tile_polygon):
                        minlat = tile_rectangle[3][0]
                        minlon = tile_rectangle[3][1]
                        maxlat = tile_rectangle[1][0]
                        maxlon = tile_rectangle[1][1]

                        f_out.write('  <bounds minlat="%.7f" minlon="%.7f" maxlat="%.7f" maxlon="%.7f" />\n' \
                                    % (minlat-0.0000001, minlon-0.0000001, maxlat+0.0000001, maxlon+0.0000001))

        f_out.write("</osm>\n")
        f_out.close

    def status(self):
        """
        print the status of the multipolygon file.
          * number and list of outer/inner polygons
          * number and list of unclosed outer and inner polygons
        """

        print ('Multipolygon of Relation %s' % (self.relation.id))
        name = self.relation.tags.get('name', '')
        if name:
            print ('  Name-Tag: ', name)
        print ('  Outer Polygons (%i):' % len(self.outer_polygons))
        for i, op in enumerate (self.outer_polygons):
            print ('    %d: %d Nodes' %(i+1, len(op)))

        print ('  Inner Polygons (%i):' % len(self.inner_polygons))
        for i, ip in enumerate (self.inner_polygons):
            print ('    %d: %d Nodes' %(i+1, len(ip)))

        print ('  Open Outer Ways (%i):' % len(self.outer_ways))
        for i, ow in enumerate (self.outer_ways):
            print ('    %d: %d Nodes, id(Node[0])=%s, id(Node[-1])=%s' %(i+1, len(ow), ow[0].id, ow[-1].id))

        print ('  Open Inner Ways (%i):' % len(self.inner_ways))
        for i, iw in enumerate (self.inner_ways):
            print ('    %d: %d Nodes, id(Node[0])=%s, id(Node[-1])=%s' %(i+1, len(iw), iw[0].id, iw[-1].id))


def usage():
    print ("usage: multipolygon.py --relation=ID [options]")
    print ("load a multipolygon from the OSM-API or from an OSM file")
    print ("export osmosis boundary polygon or check the multipolygon for errors")
    print ("-h, --help: print this usage message")
    print ("-i, --infile: osmfile to load")
    print ("-r, --relation: multipolygon relation id")
    print ("-m, --osmosispolygon: outfile for osmosis boundary polygon")
    print ("-j, --josmfile: outfile for josm boundary")


#################### MAIN
if __name__ == '__main__':
    import sys
    import getopt
    import urllib

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r:i:m:j:h',
                                   ['help', 'relation=', 'infile=', 'osmosispolygon=', 'josmfile='])
    except getopt.GetoptError:
        usage()
        sys.exit()

    mode = None
    infile = None
    osmosisfile = None
    josmfile = None
    relation = None

    for o, a in opts:
        if o in ['-i', '--infile']:
            infile = a
        elif o in ['-r', '--relation']:
            relation = a
        elif o in ['-m', '--osmosispolygon']:
            osmosisfile = a
        elif o in ['-j', '--josmfile']:
            josmfile = a
        elif o in ['-h', '--help']:
            usage()
            sys.exit()

    API='http://www.openstreetmap.org/api/0.6'

    if infile:
        osmobj = pyosm.OSMXMLFile(infile)
    elif relation:
        osmfile = urllib.urlopen('%s/relation/%s/full' %(API,relation))
        osmobj = pyosm.OSMXMLFile(osmfile)
    else:
        usage()
        sys.exit()

    mp = multipolygon(osmobj.relations[int(relation)])

    if osmosisfile:
        mp.write_osmosis_file(osmosisfile)

    elif josmfile:
        mp.write_josm_file(josmfile)

    else:
        mp.status()
