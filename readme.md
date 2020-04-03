# FileListFS - A FUSE file system for browsing lists of files

I needed to go through long lists of file paths, basically the contents
of a backup dumped a list of files and directories. So something in this form:

```
/
/bin
/bin/ls
/home
/home/johndoe
/home/johndoe/readme.txt
/usr
/usr/bin/file
```

As scanning the original file list was did not really help in getting an overview
of the backups I created a very simple FUSE-based file system that presents
the contents of a list file as a regular file system. This you can then browse
in a file manager as you usually do.

## Usage

First, create a database from a file list:

```
$ ./fill2.py list.db filelist
```

This will create a directory `list.db` holding the generated LMDB database
for all the entries in `filelist`. The file list might need to be sorted
to make this step go correct, not sure if it will handle out-of-order paths
in all cases.

You can then mount the database as a FUSE file system with

```
$ DBFILE=list.db ./filelistfs2.py <mount-point>
```

And then browse the mount-point you chose as a regular file system. 

## Notes

I originally used a [Redis](https://redis.io/) server to store all the file
information. This works quite well, but is pretty slow when browsing large
databases (millions of file entries). So a second version of the scripts used 
[LMDB](http://www.lmdb.tech/doc/) as the database. This improved browsing 
performance enormously, at the expense of database files that are about twice 
as large. The LMDB database size is usually similar to the original file list
size, or somewhat smaller, so it's not really an issue.

The fill scripts handle some ugly path details, like replacing a starting `//`
with a single `/`. 

As the files I used did not contain file size information as file sizes reported
use the same value of 12345 bytes. Similarly, no useful information on file
and directory permissions is provided in the FUSE-mounted file system.

Obviously, file *content* is not available, nor can you makes changes to the
mounted file system in any way. Although being able to delete files could be
a useful option, when cleaning up a list of files to keep only the ones of
interest. However, this isn't implemented.

## Dependencies

* Python 3.x
* [python-fuse](https://github.com/libfuse/python-fuse)
* [py-lmdb](https://github.com/jnwatson/py-lmdb) (for `fill2.py and `filelistfs2.py`)
* [redis-py](https://github.com/andymccurdy/redis-py) (for `fill.py and `filelistfs.py`)
