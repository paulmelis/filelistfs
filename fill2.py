#!/usr/bin/env python
"""
dirpath:<dirid>         -> path
dirid:<path>            -> dirid

entry:<dirid>/<entry>   -> type (0 = file, >0 = dirid)
                        <entry> must not contain a path separator
"""

import sys, time
from struct import pack, unpack
from pathlib import PurePosixPath
import lmdb

if len(sys.argv) != 3:
    print('usage: %s file.db filelist' % sys.argv[0])
    sys.exit(-1)

dbfile = sys.argv[1]
filelist = sys.argv[2]

env = lmdb.Environment(dbfile, map_size=100*1024*1024*1024)

def get_pathid(tx, path : PurePosixPath):
    
    #print('get_pathid("%s")' % path)
    
    pathstr = str(path)
    if pathstr == '/':
        return 1    
    
    parent = path.parent
    parentstr = str(parent)        
    parentid = get_pathid(tx, parent)
    
    key = 'pathid:%s' % pathstr
    key = key.encode('utf8')
    
    value = tx.get(key)
    pathid = None if value is None else unpack('<I', value)[0]
    
    if pathid is None:     
        value = tx.get(b'last_pathid')
        last_pathid = unpack('<I', value)[0]
        pathid = last_pathid + 1
        
        value = pack('<I', pathid)
        tx.put(b'last_pathid', value)
        print('New path %s (%d)' % (pathstr, pathid))
        
        tx.put(b'path:%d' % pathid, pathstr.encode('utf8'))
        
        key = 'pathid:%s' % pathstr
        key = key.encode('utf8')
        value = pack('<I', pathid)
        tx.put(key, value)
        
        # Check if corresponding entry is already marked as directory
        key = 'entry:%d/%s' % (parentid, path.name)
        key = key.encode('utf8')
        entry = tx.get(key)
        if entry is None or unpack('<I', entry)[0] == 0:
            value = pack('<I', pathid)
            tx.put(key, value)
        
    else:
        pathid = int(pathid)
        
    return pathid
    
def add_file(tx, pathid, entry):
    key = 'entry:%d/%s' % (pathid, entry)
    key = key.encode('utf8')
    value = pack('<I', 0)
    tx.put(key, value)
    
def mark_as_dir(tx, pathid, entry):
    assert pathid > 0
    key = 'entry:%d/%s' % (pathid, entry)
    key = key.encode('utf8')
    value = pack('<I', 0)
    tx.put(key, value)


with env.begin(write=True) as tx:
    
    tx.put(b'path:1', '/'.encode('utf8'))
    tx.put(b'pathid:/', pack('<I', 1))
    tx.put(b'last_pathid', pack('<I', 1))
    
    with open(filelist, 'rt') as f:
        
        for line in f:
            line = line.strip()
            
            if line == '':
                continue
                
            if line[0] == '"':
                "/usr.....;...."
                line = eval(line)            
            if line[:2] == '//':
                line = line[1:]
            # ...abc/ -> ...abc
            if line[:-1] == '/':
                line = line[:-1]
                
            if len(line) >= 512:
                print('Skipping very long path: %s' % line)
                continue
                
            #print('line', line)
            
            path = PurePosixPath(line)
            
            if line == '/':
                continue
            
            parentpath = path.parent
            entry = path.name
            assert '/' not in entry
            
            #print(path, '->', parentpath, entry)
                
            pathid = get_pathid(tx, parentpath)
                
            # Entry is file until proven otherwise
            add_file(tx, pathid, entry)

