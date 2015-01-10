#!/usr/bin/python

import sys, os
import math, re
import bz2
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from xml.sax import handler, make_parser, parseString

#################### CONSTANTS
VERSION = "0.0.2"

OSMHEAD = """<?xml version='1.0' encoding='UTF-8'?>""" \
          """<osm version="0.6" generator="osmdb 0.0.2">"""
OSMTAIL = """</osm>"""


#################### CLASSES
class SubobjectHandler(handler.ContentHandler):
    """
    simple XML Handler for osm files that extracts nodes (nd) from ways
    and members from relations
    """
    def __init__(self):
        self.relations = set([])
        self.nodes = set([])
        self.ways = set([])

    def startElement(self, obj, attrs):
        if obj == 'nd':
            self.nodes.add(int(attrs['ref']))
            return
        elif obj == 'member':
            if attrs['type'] == 'relation':
                self.relations.add(int(attrs['ref']))
            elif attrs['type'] == 'way':
                self.ways.add(int(attrs['ref']))
            elif attrs['type'] == 'node':
                self.nodes.add(int(attrs['ref']))

    def endElement(self, obj):
        pass


class Bisect(object):
    """
    Helper class for binary search processes.
    """
    def __init__(self, minindex, maxindex):
        self.min = minindex
        self.max = maxindex
        self.reset()

    def reset(self):
        """
        Setup the Bisect class or reset it to the starting stage.
        """
        self.increment = 2**int(math.log(self.max - self.min + 1, 2))
        self.cursor = self.min + self.increment - 1
        self.increment /= 2
        return self.cursor

    def up(self):
        """
        Move the cursor upwards in binary steps.
        """
        if not self.increment:
            return None
        self.cursor += self.increment
        self.increment /= 2
        while self.cursor > self.max:
            self.down()
        return self.cursor

    def down(self):
        """
        Move the cursor downwards in binary steps.
        """
        if not self.increment:
            return None
        self.cursor -= self.increment
        self.increment /= 2
        return self.cursor


class IndexBlock(object):
    """
    Artificial index object to store information about the content
    of an file index.
    """
    def __init__(self, fileindex):
        self.fileindex = fileindex
        self.first_type = None
        self.first_id = None
        self.valid = False

    def __str__(self):
        return "IndexBlock: fileindex=%s, first_type=%s, first_id=%s, valid=%s" \
            % (self.fileindex, self.first_type, self.first_id, self.valid)


class OsmDb(object):
    """
    OsmDb offers random access to large osm files that cannot be loaded
    into memomry with the pyosm class.
    Basically it creates a file index on the fly and binary search system
    to find objects in large files really fast.
    """
    def __init__(self, filename):
        self.filename = filename
        self._index = []

        self._filesize = os.path.getsize(self.filename)
        self._filehandler = open(self.filename, 'rb')
        self._create_index()

    def _create_index(self):
        """
        Allocate index blocks without validating them.
        """
        CNT = 100000
        self._index =  [ IndexBlock( i * CNT ) for i in xrange(self._filesize / CNT - 1 ) ]

    def _validate(self, blk):
        """
        Find the first object element in the block and update the block index.
        Returns False if the block has no object item.
        """
        if blk.valid:
            return True

        self._filehandler.seek(blk.fileindex)
        while True:
            line = self._filehandler.readline()
            if line == False: ## EOF or Error
                return False
            else:
                for obj in ['node', 'way', 'relation']:
                    if re.match('[ \t]*<%s id="[0-9]*" ' % obj, line):
                        blk.first_type = obj
                        blk.first_id = int(line.split('"')[1])
                        blk.valid = True
                        return True

    def _get_block(self, objtype, objid):
        """
        Search the index-block, that contains the given objtype and objid.
        This performs a binary search through the file.
        """
        sortorder = {'node': 0, 'way': 1, 'relation': 2}
        bisect = Bisect(0, len(self._index)-1)
        blocknr = bisect.reset()
        while True:
            blk = self._index[blocknr]
            if not self._validate(blk):
                self._index.pop(blocknr)
                log("bad block: %s" % blocknr)
                bisect = Bisect(0, len(self._index)-1)
                blocknr = bisect.reset()
                continue

            log("bisect Nr=%s, seeking %s=%s" %(blocknr, objtype, objid), str(blk))

            res = cmp((sortorder[objtype], objid),
                      (sortorder.get(blk.first_type, 100), blk.first_id))

            if res < 0:
                if blocknr != 0 and self._index[blocknr-1].valid:
                    blk2 = self._index[blocknr-1]
                    if blk2.valid and ((sortorder[objtype], objid) >= \
                                           (sortorder[blk2.first_type], blk2.first_id)):
                        return blk2
                blocknr = bisect.down()
            elif res == 0:   ## exact match (rare case)
                return blk
            else:
                if blocknr == len(self._index)-1:
                    return blk
                blk2 = self._index[blocknr+1]
                if blk2.valid and ((sortorder[objtype], objid) < \
                                       (sortorder[blk2.first_type], blk2.first_id)):
                    return blk
                blocknr = bisect.up()

    def print_index(self):
        """
        debug function to print all index items
        """
        for i,b in enumerate(self._index):
            print i, str(b)

    def write_relations(self, filename):
        """
        Write all relations of the osm fileobject to the given filename.
        If the filename ends with ".bz2", then the relations will be compressed.
        With filename=/dev/stdout you can get a stream of all realations.
        """
        log("OsmDb: writing relations")

        blk = self._get_block('relation', 0)
        self._filehandler.seek(blk.fileindex)

        while True:
            line = self._filehandler.readline()
            if re.match('[ \t]*<relation id="[0-9]*" ', line):
                break

        if filename[-4] == '.bz2':
            fout = bz2.BZ2File(filename, 'w')
        else:
            fout = open(filename, 'w')
        fout.write(OSMHEAD + '\n' + line)
        while True:
            data = self._filehandler.read(10000000)
            if not data:
                break
            fout.write(data)
        fout.close()
        log("OsmDb: writing relations complete")

    def write_ways_relations(self, filename):
        """
        Write all ways and relations of the osm fileobject to the given filename.
        If the filename ends with ".bz2", then the relations will be compressed.
        With filename=/dev/stdout you can get a stream of all realations.
        """
        log("OsmDb: writing ways and relations")

        blk = self._get_block('way', 0)
        self._filehandler.seek(blk.fileindex)

        while True:
            line = self._filehandler.readline()
            if re.match('[ \t]*<way id="[0-9]*" ', line):
                break

        if filename[-4] == '.bz2':
            fout = bz2.BZ2File(filename, 'w')
        else:
            fout = open(filename, 'w')
        fout.write(OSMHEAD + '\n' + line)
        while True:
            data = self._filehandler.read(10000000)
            if not data:
                break
            fout.write(data)
        fout.close()
        log("OsmDb: writing ways and relations complete")

    def get_objects_recursive(self, objtype, ids=[], recursive=False):
        """
        Recursively get all osm objects that are listed in the ids.
        If recursive=False, then you get only the objects that are directly
        referenced in relations.
        If recursive=True, then you get all hierarchically referenced
        from the relations.
        """
        relationids = set([])
        wayids = set([])
        nodeids = set([])
        relationdata, waydata, nodedata = '','',''

        if objtype == 'node':
            nodids = set(ids)
        elif objtype == 'way':
            wayids = set(ids)
        elif objtype == 'relation':
            relationids = set(ids)
        else:
            return ""

        if recursive:
            recursions = 100  # maximum recursion level
        else:
            recursions = 1    # only get all direct members

        loaded_relationids = set([])
        while relationids:
            r_data = self.get_objects('relation', relationids)
            relationdata += '\n' + r_data

            if not recursions:
                break
            else:
                recursions -= 1

            parser = make_parser()
            osm_handler = SubobjectHandler()
            parser.setContentHandler(osm_handler)
            parseString(OSMHEAD + r_data + OSMTAIL, osm_handler)
            nodeids |= osm_handler.nodes
            wayids |= osm_handler.ways
            loaded_relationids |= relationids
            relationids = osm_handler.relations - loaded_relationids

        if wayids:
            waydata = self.get_objects('way', wayids)
            parser = make_parser()
            osm_handler = SubobjectHandler()
            parser.setContentHandler(osm_handler)
            parseString(OSMHEAD + waydata + OSMTAIL, osm_handler)
            nodeids |= osm_handler.nodes

        if nodeids:
            nodedata = self.get_objects('node', nodeids)

        return nodedata + waydata + relationdata

    def get_objects(self, objtype, ids=[]):
        """
        get all osm objects listed in ids with the given object type.
        The object type is one of [relation, way, node].
        """
        objids = sorted(ids)
        datalines = []
        lastid = objids[0] - 10000
        for objid in objids:
            log(objtype, objid)
            if objid > lastid + 1000:
                blk = self._get_block(objtype, objid)
                self._filehandler.seek(blk.fileindex)
            lastid = objid
            while True:
                line = self._filehandler.readline()
                if re.match('[ \t]*<%s id="[0-9]*" ' % objtype, line):
                    lineid = int(line.split('"')[1])
                    if lineid < objid:
                        continue
                    elif lineid == objid:
                        datalines.append(line)
                        break
                    elif lineid > objid:
                        line = ""
                        print objtype, objid, "not found"
                        lastid = objid - 10000
                        break
            if line == "":
                continue
            if line[-3:] == '/>\n':
                continue
            while True:
                line = self._filehandler.readline()
                datalines.append(line)
                if re.match('[ \t]*</%s>' %objtype, line):
                    break
        return ''.join(datalines)


class Bz2Reader(object):
    """
    Helper class to access a bz2-compressed file like an uncompressed file.
    """
    def __init__(self, filehandler, bz2filehead, bz2filesize):
        self._filehandler = filehandler
        self.__filehead = bz2filehead
        self._filesize = bz2filesize

    def changeblock(self, bz2block):
        """
        Reset the reader cursor to another block index.
        """
        self.__blk = bz2block
        self.__bz2dc = bz2.BZ2Decompressor()
        self.__bz2dc.decompress(self.__filehead)
        self.__bz2cursor = self.__blk.fileindex
        self.__databuffer = ""
        self.__datacursor = 0

    def __readbz2(self, size):
        """
        Read data with the given size from the bz2-file.
        The size is defined in the compressed context of the bz2-file
        """
        self._filehandler.seek(self.__bz2cursor)
        if self.__bz2cursor == self._filesize - 5:
            return 'EOF'
        if self.__bz2cursor + size >= self._filesize - 5:
            size = self._filesize - self.__bz2cursor - 5
        datain = self._filehandler.read(size)
        while datain:
            try:
                self.__databuffer += self.__bz2dc.decompress(datain)
            except EOFError, msg:
                log(msg, len(self.__bz2dc.unused_data))
                if len(self.__bz2dc.unused_data) > 4:
                    log("unused head", self.__bz2dc.unused_data[:4])
                datain = self.__bz2dc.unused_data
                self.__bz2dc = bz2.BZ2Decompressor()
                continue
            except Exception, msg:
                log(msg)
                return False
            break

        self.__bz2cursor = self._filehandler.tell()
        return True

    def read(self, size):
        """
        Read the given number of bytes from the bz2-file
        The size is defined in uncompressed bytes.
        """
        while (len(self.__databuffer) - self.__datacursor) < size:
            res = self.__readbz2(size / 20)
            if res == 'EOF':
                data = self.__databuffer[self.__datacursor:]
                self.__databuffer = ""
                self.__datacusor = 0
                if data:
                    return data
                else:
                    return False
            if not res:
                return False

        data = self.__databuffer[self.__datacursor:self.__datacursor + size]
        self.__datacursor += size

        if self.__datacursor > 2*size:
            self.__databuffer = self.__databuffer[self.__datacursor:]
            self.__datacursor = 0

        return data

    def readline(self):
        """
        Read a line from the bz2reader
        """
        while True:
            ind = self.__databuffer.find('\n', self.__datacursor)
            if ind == -1:
                res = self.__readbz2(10000)
                if not res:
                    return False
            else:
                line = self.__databuffer[self.__datacursor:ind]
                self.__datacursor = ind + 1
                break

        if self.__datacursor > 100000:
            self.__databuffer = self.__databuffer[self.__datacursor:]
            self.__datacursor = 0
        return line


class Bz2OsmDb(OsmDb):
    """
    Bz2OsmDb offers random access to large bz2 compressed osm files that
    cannot be loaded into memomry with the pyosm class.
    Basically it creates a file index on the fly and binary search system
    to find objects in large files really fast.
    The API is identical to the OsmDb class.
    Note: This class cannot access multistream bz2 files
          see http://bugs.python.org/issue1625 for details
    """
    def __init__(self, bz2filename):
        self.bz2filename = bz2filename
        self._index = []

        self._filesize = os.path.getsize(self.bz2filename)
        self._filehandler = open(self.bz2filename, 'rb')
        self._bz2_filehead = self._filehandler.read(4)
        log("file head:", str(self._bz2_filehead))

        self._create_index()
        self._bz2reader = Bz2Reader(self._filehandler, self._bz2_filehead, self._filesize)

    def _create_index(self):
        """
        Create an index for the compressed osm file
        """
        BZ2_COMPRESSED_MAGIC = chr(0x31)+chr(0x41)+chr(0x59)+chr(0x26)+chr(0x53)+chr(0x59)
        READBLOCK_SIZE = 100000000
        log("Bz2OsmDb: creating index")
        fin = self._filehandler
        block_nr = 0
        while True:
            cursor = 0
            fin.seek(block_nr * READBLOCK_SIZE)
            buf = fin.read(READBLOCK_SIZE+10)
            while True:
                found = buf.find(BZ2_COMPRESSED_MAGIC, cursor)
                if found == -1:
                    break
                block = IndexBlock(block_nr * READBLOCK_SIZE + found)
                self._index.append(block)
                cursor = found + 2
            block_nr += 1
            if fin.tell() < block_nr * READBLOCK_SIZE:
                break

        log("Bz2OsmDb: index complete: %d Blocks" % len(self._index))

    def _validate(self, blk):
        """
        Find the first object element in the block and update the block index.
        Returns False if the block has no object item.
        """
        if blk.valid:
            return True

        self._bz2reader.changeblock(blk)
        while True:
            line = self._bz2reader.readline()
            if line == False: ## EOF or Error
                return False
            else:
                for obj in ['node', 'way', 'relation']:
                    if re.match('[ \t]*<%s id="[0-9]*" ' % obj, line):
                        blk.first_type = obj
                        blk.first_id = int(line.split('"')[1])
                        blk.valid = True
                        return True

    def write_relations(self, filename):
        """
        Write all relations of the osm fileobject to the given filename.
        If the filename ends with ".bz2", then the relations will be compressed.
        With filename=/dev/stdout you can get a stream of all realations.
        """
        log("Bz2OsmDb: writing relations")
        OSMHEAD = """<?xml version='1.0' encoding='UTF-8'?>\n""" \
                  """<osm version="0.6" generator="Osmosis 0.32">"""
        blk = self._get_block('relation', 0)
        self._bz2reader.changeblock(blk)

        if filename[-4:] == '.bz2':
            fout = bz2.BZ2File(filename, 'w')
        else:
            fout = open(filename, 'w')

        while True:
            line = self._bz2reader.readline()
            if re.match('[ \t]*<relation id="[0-9]*" ', line):
                break

        fout.write(OSMHEAD + '\n' + line + '\n')
        while True:
            data = self._bz2reader.read(10000000)
            if not data:
                break
            fout.write(data)
        fout.close()
        log("Bz2OsmDb: relation writing complete")

    def write_ways_relations(self, filename):
        """
        Write all ways and relations of the osm fileobject to the given filename.
        If the filename ends with ".bz2", then the relations will be compressed.
        With filename=/dev/stdout you can get a stream of all realations.
        """
        log("Bz2OsmDb: writing relations")
        OSMHEAD = """<?xml version='1.0' encoding='UTF-8'?>\n""" \
                  """<osm version="0.6" generator="Osmosis 0.32">"""
        blk = self._get_block('way', 0)
        self._bz2reader.changeblock(blk)

        if filename[-4:] == '.bz2':
            fout = bz2.BZ2File(filename, 'w')
        else:
            fout = open(filename, 'w')

        while True:
            line = self._bz2reader.readline()
            if re.match('[ \t]*<way id="[0-9]*" ', line):
                break

        fout.write(OSMHEAD + '\n' + line + '\n')
        while True:
            data = self._bz2reader.read(10000000)
            if not data:
                break
            fout.write(data)
        fout.close()
        log("Bz2OsmDb: relation writing complete")

    def get_objects(self, objtype, ids=[]):
        """
        get all osm objects listed in ids with the given object type.
        The object type is one of [relation, way, node].
        """
        objids = sorted(ids)
        datalines = []
        lastid = objids[0] - 10000
        for objid in objids:
            log(objtype, objid)
            if objid > lastid + 1000:
                blk = self._get_block(objtype, objid)
                self._bz2reader.changeblock(blk)
            lastid = objid
            while True:
                line = self._bz2reader.readline()
                if re.match('[ \t]*<%s id="[0-9]*" ' % objtype, line):
                    lineid = int(line.split('"')[1])
                    if lineid < objid:
                        continue
                    elif lineid == objid:
                        datalines.append(line)
                        break
                    elif lineid > objid:
                        line = ""
                        break
            if line == "":
                continue
            if line[-2:] == '/>':
                continue
            while True:
                line = self._bz2reader.readline()
                datalines.append(line)
                if re.match('[ \t]*</%s>' %objtype, line):
                    break
        return '\n'.join(datalines)


class OSMHttpHandler(BaseHTTPRequestHandler):
    """
    HTTP handler URL commands from the HTTP server.
    """
    def print_help(self):
        self.send_response(404)
        self.send_header('Content-type',	'text/html')
        self.end_headers()
        self.wfile.write("OSMDB File interface<br>")
        self.wfile.write("=====================<br><br>")
        self.wfile.write("valid commands are:<br><br>")
        self.wfile.write("  nodes?nodes=id1,id2,...<br>")
        self.wfile.write("  ways?ways=id1,id2,...<br>")
        self.wfile.write("  relations?relations=id1,id2,...<br>")
        self.wfile.write("  ways?ways=id1,id2,...&mode=full<br>")
        self.wfile.write("  relations?relations=id1,id2,...&mode=full<br>")
        self.wfile.write("  relations?relations=id1,id2,...&mode=recursive")
        return

    def do_GET(self):
        print self.path
        osm = self.server.osmdb
        toks = self.path.split('?')
        if len(toks) != 2:
            self.print_help()
            return
        else:
            command = toks[0]
            kvs = toks[1].split('&')
            args = dict([kv.split('=',1) for kv in kvs])
        try:
            if command == '/nodes':
                nodes = [int(n) for n in args['nodes'].split(',')]
                data = osm.get_objects('node', nodes)
            elif command == '/ways':
                ways = [int(n) for n in args['ways'].split(',')]
                if args.get('mode','') == 'full':
                    data = osm.get_objects_recursive('way', ways)
                else:
                    data = osm.get_objects('way', ways)
            elif command == '/relations':
                relations = [int(n) for n in args['relations'].split(',')]
                if args.get('mode','') == 'full':
                    data = osm.get_objects_recursive('relation', relations)
                elif args.get('mode','') == 'recursive':
                    data = osm.get_objects_recursive('relation', relations, recursive=True)
                else:
                    data = osm.get_objects('relation', relations)
            self.send_response(200)
            self.send_header('Content-type',	'text/xml')
            self.end_headers()
            self.wfile.write(OSMHEAD+'\n')
            self.wfile.write(data)
            self.wfile.write('</osm>')
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


################### FUNCTIONS
def runserver(port, osmdb):
    """
    Start the http-server with the given port and osmdb object.
    """
    try:
        server = HTTPServer(('', port), OSMHttpHandler)
        server.osmdb = osmdb
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

def log(*args):
    """ simple helper function for debugging"""
    return
    for a in args:
        print a,
    print

def usage():
    print sys.argv[0] + " Version " + VERSION
    print "  -h, --help: print this help information"
    print "  --relations=outfile: split relations from input file"
    print "  --ways_relations=outfile: split ways and relations from input file"
    print "  --server=port: start a http-Server on Port"
    print "Examples:"
    print "  osmdb.py --relations=out.osm.bz2 germany.osm.bz2"
    print "  osmdb.py --ways_relations=/dev/stdout planet-latest.osm"
    print "  osmdb.py --server=8888 germany.osm"


#################### MAIN
if __name__ == '__main__':
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['relations=', 'ways_relations=', 'server=', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit()


    for o, a in opts:
        if o in ['--relations']:
            if len(args) != 1:
                usage()
                sys.exit(-1)
            outfile = a
            if os.path.splitext(args[0])[1] in ['.bz2','.BZ2']:
                osmdb = Bz2OsmDb(args[0])
            else:
                osmdb = OsmDb(args[0])
            osmdb.write_relations(outfile)
            sys.exit()
        elif o in ['--ways_relations']:
            if len(args) != 1:
                usage()
                sys.exit(-1)
            outfile = a
            if os.path.splitext(args[0])[1] in ['.bz2','.BZ2']:
                osmdb = Bz2OsmDb(args[0])
            else:
                osmdb = OsmDb(args[0])
            osmdb.write_ways_relations(outfile)
            sys.exit()
        elif o in ['--server']:
            if len(args) != 1:
                usage()
                sys.exit(-1)
            port = int(a)
            if os.path.splitext(args[0])[1] in ['.bz2','.BZ2']:
                osmdb = Bz2OsmDb(args[0])
            else:
                osmdb = OsmDb(args[0])
            runserver(port, osmdb)
            sys.exit()
        elif o in ['--help']:
            usage()
            sys.exit()
