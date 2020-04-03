#!/usr/bin/env python

# This file is based on example/hello.py in the python-fuse repository
# at https://github.com/libfuse/python-fuse.
#
# The original copyright disclaimer for hello.py is this:
#
#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#
# See the python-fuse repository for more information.

import sys, os, stat, errno
from pathlib import PurePosixPath

import fuse
if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")
from fuse import Fuse
    
import redis

fuse.fuse_python_api = (0, 2)

logfile = open('log.fuse', 'wt')

def log(s):
    logfile.write(s+'\n')
    logfile.flush()

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class FileListFS(Fuse):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = redis.StrictRedis('localhost', charset="utf-8", decode_responses=True)

    def getattr(self, path):
        log('getattr("%s")' % path)
        
        path = PurePosixPath(path)
        
        st = MyStat()
        
        pathid = self.redis.get('pathid:%s' % path)
        if pathid is not None:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            return st
            
        parentpath = path.parent
        parentid = self.redis.get('pathid:%s' % parentpath)
        if parentid is not None:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = 12345            
            return st
            
        return -errno.ENOENT
            
            
    def readdir(self, path, offset):
        log('readdir("%s", %d)' % (path, offset))
        
        pathid = self.redis.get('pathid:%s' % path)
        if pathid is None:        
            return -errno.ENOENT
            
        pathid = int(pathid)
        
        entries = [e.split('/')[-1] for e in self.redis.keys('entry:%d/*' % pathid)]
        entries.insert(0, '..')
        entries.insert(0, '.')
        
        log(str(entries))
        for r in entries:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        log('open("%s", %d)' % (path, flags))
        return -errno.EACCES

    def read(self, path, size, offset):
        log('read("%s", %d, %d)' % (path, size, offset))
        return b''

def main():
    usage="""
Userspace hello example

""" + Fuse.fusage

    server = FileListFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
