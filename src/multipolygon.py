#!/usr/bin/python

import sys
import pyosm
import numpy
import matplotlib.nxutils

class multipolygon(object):

    def __init__(self, relation):
        self.relation = relation
        self.read_relation(self.relation)

    def read_relation(self, relation):
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
            way = endnodes[endnodes.keys()[0]][0]
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
                if type(obj) == pyosm.Relation:
                    todo_stack.append(m)
                else:
                    members.append(m)

        return members

    def inside(self, nodes):
        points = self.pointlist(nodes)
        matches = numpy.zeros(len(points))
        for outerpoly in self.outer_polygons:
            outerpoints = self.pointlist(outerpoly)
            matches = matches + matplotlib.nxutils.points_inside_poly(points, outerpoints)
        for innerpoly in self.inner_polygons:
            innerpoints = self.pointlist(innerpoly)
            matches = matches - matplotlib.nxutils.points_inside_poly(points, innerpoints)
        return matches

    def pointlist(self, nodes):
        points = []
        for node in nodes:
            points.append((float(node.lon), float(node.lat)))
        return points

    def status(self):

        print 'Multipolygon of Relation %s' % (self.relation.id)
        print '  Outer Polygons (%i):' % len(self.outer_polygons)
        for i, op in enumerate (self.outer_polygons):
            print '    %d: %d Nodes' %(i, len(op))

        print '  Inner Polygons (%i):' % len(self.inner_polygons)
        for i, ip in enumerate (self.inner_polygons):
            print '    %d: %d Nodes' %(i, len(ip))

        print '  Open Outer Ways (%i):' % len(self.outer_ways)
        for i, ow in enumerate (self.outer_ways):
            print '    %d: %d Nodes, id(Node[0])=%s, id(Node[-1])=%s' %(i, len(ow), ow[0].id, ow[-1].id)

        print '  Open Inner Ways (%i):' % len(self.inner_ways)
        for i, iw in enumerate (self.inner_ways):
            print '    %d: %d Nodes, id(Node[0])=%s, id(Node[-1])=%s' %(i, len(iw), iw[0].id, iw[-1].id)


#################### MAIN
if __name__ == '__main__':
    import getopt
    import urllib

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r:i:m:',
                                   ['relation=', 'infile=', 'osmosispolygon'])
    except getopt.GetoptError:
        usage()
        sys.exit()

    mode = None
    infile = None
    osmosisfile = None
    relation = None

    for o, a in opts:
        if o in ['-i', '--infile']:
            infile = a
        elif o in ['-o', '--outfile']:
            outfile = a
        elif o in ['-r', 'relation']:
            relation = a
        elif o in ['-m', 'osmosispolygon']:
            osmosisfile = a
        


    API='http://www.openstreetmap.org/api/0.6'

    if infile:
        osmobj = pyosm.OSMXMLFile(infile)
    else:
        osmfile = urllib.urlopen('%s/relation/%s/full' %(API,relation))
        osmobj = pyosm.OSMXMLFile(osmfile)

    mp = multipolygon(osmobj.relations[relation])

    if osmosisfile:
        fd = open(osmosisfile, 'wt')
        n = 1
        fd.write('xxx\n')
        for op in mp.outer_polygons:
            fd.write('%i\n' %(n))
            for node in op:
                fd.write('\t%s\t%s\n' %(node.lon, node.lat))
            fd.write('END\n')
            n += 1
            
        for op in mp.inner_polygons:
            fd.write('xxx\n')
            fd.write('!%i\n' %(n))
            for node in op:
                fd.write('\t%f\t%f\n' %(node.lat, node.lon))
            fd.write('END\n')
            n += 1
        fd.write('END\n')
    
    mp.status()

    
