#!/usr/bin/env python
"""
dirpath:<dirid>         -> path
dirid:<path>            -> dirid

entry:<dirid>/<entry>   -> type (0 = file, >0 = dirid)
                        <entry> must not contain a path separator
"""

import sys, redis, time
from pathlib import PurePosixPath

r = redis.StrictRedis('localhost', charset="utf-8", decode_responses=True)
r.flushall()
r.set('path:1', '/')
r.set('pathid:/', 1)
r.set('last_pathid', 1)

def get_pathid(path : PurePosixPath):
    
    #print('get_pathid("%s")' % path)
    
    pathstr = str(path)
    if pathstr == '/':
        return 1    
    
    parent = path.parent
    parentstr = str(parent)        
    parentid = get_pathid(parent)
    
    pathid = r.get('pathid:%s' % pathstr)
    
    if pathid is None:                  
        pathid = int(r.incr('last_pathid'))
        print('New path %s (%d)' % (pathstr, pathid))
        
        r.set('path:%d' % pathid, pathstr)
        r.set('pathid:%s' % pathstr, pathid)
        
        # Check if corresponding entry is already marked as directory
        key = 'entry:%d/%s' % (parentid, path.name)
        entry = r.get(key)
        if entry is None or int(entry) == 0:
            r.set(key, pathid)
        
    else:
        pathid = int(pathid)
        
    return pathid
    
def add_file(pathid, entry):    
    r.set('entry:%d/%s' % (pathid, entry), 0)
    
def mark_as_dir(pathid, entry):
    assert pathid > 0
    r.set('entry:%d/%s' % (pathid, entry), 0)


with open(sys.argv[1], 'rt') as f:
    
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
            
        #print('line', line)
        
        path = PurePosixPath(line)
        
        if line == '/':
            continue
        
        parentpath = path.parent
        entry = path.name
        assert '/' not in entry
        
        #print(path, '->', parentpath, entry)
            
        pathid = get_pathid(parentpath)
            
        # Entry is file until proven otherwise
        add_file(pathid, entry)

