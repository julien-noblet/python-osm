#!/usr/bin/python

import sys, os
import math, re, exceptions
import bz2



class Bisect(object):
    def __init__(self, minindex, maxindex):
        self.min = minindex
        self.max = maxindex
        self.reset()

    def reset(self):
        self.increment = 2**int(math.log(self.max - self.min + 1, 2))
        self.cursor = self.min + self.increment - 1
        self.increment /= 2
        return self.cursor
        
    def up(self):
        if not self.increment:
            return None
        self.cursor += self.increment
        self.increment /= 2
        while self.cursor > self.max:
            self.down()
        return self.cursor

    def down(self):        
        if not self.increment:
            return None
        self.cursor -= self.increment
        self.increment /= 2
        return self.cursor


class Bz2Block(object):
    def __init__(self, fileindex):
        self.fileindex = fileindex
        self.first_type = None
        self.first_id = None
        self.valid = False

    def __str__(self):
        return "Bz2Block: fileindex=%s, first_type=%s, first_id=%s, valid=%s" \
            % (self.fileindex, self.first_type, self.first_id, self.valid)


class Bz2OsmDb(object):
    def __init__(self, bz2filename):
        self.bz2filename = bz2filename
        self.__bz2blocks = []

        self.__filesize = os.path.getsize(self.bz2filename)
        self.__filehandler = open(self.bz2filename, 'rb')
        self.__bz2_filehead = self.__filehandler.read(4)
        print "file head:", str(self.__bz2_filehead)

        self.__create_index()

    def __create_index(self):
        BZ2_COMPRESSED_MAGIC = chr(0x31)+chr(0x41)+chr(0x59)+chr(0x26)+chr(0x53)+chr(0x59)
        READBLOCK_SIZE = 100000000
        print "Bz2OsmDb: creating index"
        fin = self.__filehandler
        block_nr = 0
        while True:
            cursor = 0
            fin.seek(block_nr * READBLOCK_SIZE)
            buf = fin.read(READBLOCK_SIZE+10)
            while True:
                found = buf.find(BZ2_COMPRESSED_MAGIC, cursor)
                if found == -1:
                    break
                block = Bz2Block(block_nr * READBLOCK_SIZE + found)
                self.__bz2blocks.append(block)
                cursor = found + 2
            block_nr += 1
            if fin.tell() < block_nr * READBLOCK_SIZE:
                break

        print "Bz2OsmDb: index complete: %d Blocks" % len(self.__bz2blocks)


    def __validate(self, blk):
        if blk.valid:
            return True

        self.__bz2readerinit(blk)
        while True:
            line = self.__readline(blk)
            if line == False: ## EOF or Error
                return False
            else:
                for obj in ['node', 'way', 'relation']:
                    if re.match('  <%s id="[0-9]*" ' % obj, line):
                        blk.first_type = obj
                        blk.first_id = int(line.split('"')[1])
                        blk.valid = True
                        return True

    def __bz2readerinit(self, blk):
        self.bz2dc = bz2.BZ2Decompressor()
        self.bz2dc.decompress(self.__bz2_filehead)
        self.bz2cursor = blk.fileindex
        self.databuffer = ""
        self.datacursor = 0

    def __readbz2(self, size):
        self.__filehandler.seek(self.bz2cursor)
        if self.bz2cursor == self.__filesize - 5:
            return 'EOF'
        if self.bz2cursor + size >= self.__filesize - 5:
            size = self.__filesize - self.bz2cursor - 5
        try:
            self.databuffer += self.bz2dc.decompress(self.__filehandler.read(size))
        except Exception, e:
            print e
            return False
        
        self.bz2cursor = self.__filehandler.tell()
        return True
        
    def __read(self, blk, size):
        while (len(self.databuffer) - self.datacursor) < size:
            res = self.__readbz2(size / 20)
            if res == 'EOF':
                data = self.databuffer[self.datacursor:]
                self.databuffer = ""
                self.datacusor = 0
                if data:
                    return data
                else:
                    return False
            if not res:
                return False

        data = self.databuffer[self.datacursor:self.datacursor + size]
        self.datacursor += size

        if self.datacursor > 2*size:
            self.databuffer = self.databuffer[self.datacursor:]
            self.datacursor = 0

        return data

    def __readline(self, blk):
        while True:
            ind = self.databuffer.find('\n', self.datacursor)
            if ind == -1:
                res = self.__readbz2(10000)
                if not res:
                    return False
            else:
                line = self.databuffer[self.datacursor:ind]
                self.datacursor = ind + 1
                break

        if self.datacursor > 100000:
            self.databuffer = self.databuffer[self.datacursor:]
            self.datacursor = 0
        return line

    def __get_block(self, objtype, objid):
        sortorder = {'node': 0, 'way': 1, 'relation': 2}
        bisect = Bisect(0, len(self.__bz2blocks)-1)
        blocknr = bisect.reset()
        while True:
            blk = self.__bz2blocks[blocknr]
            if not self.__validate(blk):
                self.__bz2blocks.pop(blocknr)
                print "bad block: %s" % blocknr
                bisect = Bisect(0, len(self.__bz2blocks)-1)
                blocknr = bisect.reset()
                continue

            print "bisect Nr=%s, seeking %s=%s" %(blocknr, objtype, objid), str(blk)

            res = cmp((sortorder[objtype], objid), 
                      (sortorder.get(blk.first_type, 100), blk.first_id))

            if res < 0:
                if blocknr != 0 and self.__bz2blocks[blocknr-1].valid:
                    blk2 = self.__bz2blocks[blocknr-1]
                    if blk2.valid and ((sortorder[objtype], objid) >= \
                                           (sortorder[blk2.first_type], blk2.first_id)):
                        return blk2
                blocknr = bisect.down()
            elif res == 0:   ## exact match (rare case)
                return blk
            else:
                if blocknr == len(self.__bz2blocks)-1:
                    return blk
                blk2 = self.__bz2blocks[blocknr+1]
                if blk2.valid and ((sortorder[objtype], objid) < \
                                       (sortorder[blk2.first_type], blk2.first_id)):
                    return blk
                blocknr = bisect.up()

    def print_index(self):
        for i,b in enumerate(self.__bz2blocks):
            print i, str(b)
    
    def write_relations(self, filename):
        print "Bz2OsmDb: writing relations"
        OSMHEAD = """<?xml version='1.0' encoding='UTF-8'?>""" \
                  """<osm version="0.6" generator="Osmosis 0.32">"""
        blk = self.__get_block('relation', 0)
        self.__bz2readerinit(blk)

        while True:
            line = self.__readline(blk)
            if re.match('  <relation id="[0-9]*" ', line):
                break

        fout = bz2.BZ2File(filename, 'w')
        fout.write(OSMHEAD + '\n' + line + '\n')
        while True:
            data = self.__read(blk, 10000000)
            if not data:
                break
            fout.write(data)
        fout.close()
        print "Bz2OsmDb: relation writing complete"

    def get_objects(self, relations=[], ways=[], nodes=[]):
        data = []
        for r in sorted(relations):
            xx = 1
        for w in sorted(ways):
            xx = 1
        for n in sorted(nodes):
            xx = 1
      

def usage():
    xx=1

if __name__ == '__main__':
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['relations=', 'reversed=', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit()

    if not len(args) != 1:
        usage()

    for o, a in opts:
        if o in ['--relations']:
            outfile = a
            osmdb = Bz2OsmDb(args[0])
            osmdb.write_relations(outfile)
            sys.exit()
        elif o in ['--reversed']:
            outfile = a
            osmdb = Bz2OsmDb(args[0])
            osmdb.write_reversed(outfile)
            sys.exit()
            
