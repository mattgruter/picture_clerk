#!/usr/bin/env python
from __future__ import with_statement
"""pic.py

PictureClerk - The little helper for your picture workflow.
Command line interface
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/06/15 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"

import os
import fnmatch
import shelve

from recipe import *
from worker import *
from pipeline import *
from picture import *
from config import *


def read_cache(cache, verbose):
    # TODO: catch exceptions
    try:
        pics = cache['pics']
    except KeyError:
        print "Cache file unreadable."
        sys.exit(2)
    return pics
        
        
def write_cache(cache, pics, verbose):
    # TODO: catch exceptions
    cache['pics'] = pics


def import_dir(path, verbose):
    # TODO: use os.walk to search for files recursively
    dirlist = os.listdir(path)
    # TODO: what files to import? check that only NEF files are present so that
    #       already present sidecar files are not overwritten. or maybe,
    #       analyze directory and add present sidecar files (=same basename) to
    #       picture instance.
    files = fnmatch.filter(dirlist, config.IMPORT_FILE_PATTERN)
    if not files:
        if verbose:
            print 'No picture files found. Exiting.'
        return
    files = [ os.path.join(path, f) for f in files ]
    pics = [ Picture(f) for f in files ]

    instructions = [Exiv2MetadataWorker, DCRawThumbWorker, HashDigestWorker, AutorotWorker]
    recipe = Recipe(instructions)

    pl = Pipeline('Pipeline1', recipe)
    for pic in pics:
        pl.put(pic)
    pl.start()
    # waits until all jobs are completed.
    pl.join()
    # FIXME: repalce pl.join with a while pl.isactive loop with progress
    # display. For this pl.isactive has to be set to False after all jobs have
    # completed...
#    while pl.isactive:
#        print pl.get_progress()
    
    return pics
    

def list_pics(pics, verbose):
    for pic in pics:
        print pic
        
        
def path2pic(files, pics, verbose):
    return [pic for pic in pics if pic.path in files]
    
        
def clean_pics(pics, verbose):
    for pic in pics:
        if verbose:
            print 'Removing all associated sidecar files of %s.' % pic.path
        for s in pic._sidecars:
            try:
                os.remove(s.path)
            except OSError:
                # FIXME: shouldn't fail if file is not present (we just don't
                #        care then), but it should fail if we can't remove the
                #        file due to wrong permissions.
                print 'Error: Unable to remove sidecar file %s.' % s.path
                sys.exit(1)
        pic._sidecars = []


def clean_dir(pics, cache_file, verbose):
    clean_pics(pics, verbose)
    if verbose: print 'Removing local cache file %s.' % cache_file
    try:
        os.remove(cache_file)
    except OSError:
        print 'Error: Unable to remove cache file %s.' % cache_file
        sys.exit(1)
        
        
def delete_pics(selection, pics, verbose):
    clean_pics(selection, verbose)
    for pic in selection:
        if verbose:
            print 'Removing %s.' % pic.path
        try:
            pics.remove(pic)
            os.remove(pic.path)
        except KeyError, OSError:
            print 'Error: Unable to remove %s.' % s.path
            sys.exit(1)    
    return pics
    

def show_dir(pics, verbose):
    if verbose:
        print 'Starting image viewer QIV...'
    args = [ 'qiv', '-t']
    args.extend(sorted(pic.thumbnail for pic in pics))
    try:
        viewer_process = subprocess.Popen(args, shell=False)
        retcode = viewer_process.wait()
        #retcode = subprocess.call(args, shell=False)
        if retcode < 0:
            print >>sys.stderr, "Child was terminated by signal", -retcode
    except OSError, e:
        print >>sys.stderr, "Execution failed:", e
    
    
def list_checksums(pics, verbose):
    output = ('%s  %s' % (p.basename+p.extension, p.checksum) for p in pics)
    for line in output:
        print line
    
    
def check_dir(pics, verbose):
    # TODO: use worker threads to check checksums
    import hashlib
    for pic in pics:
        try:
            with open(pic.path, 'rb') as pic_file:
                _buf = pic_file.read()
        except IOError:
            print 'NOT FOUND: %s' % pic.filename
            continue
        _digest = hashlib.sha1(_buf).hexdigest()
        if _digest != pic.checksum:
            print 'FAILED:    %s' % pic.filename
        elif verbose:
            print 'OK:        %s' % pic.filename
      

def update_dir(pics, path, verbose):
    pass


def main():
    from optparse import OptionParser

    usage = "usage: %prog [OPTIONS] ARG1 ARG2"
    parser = OptionParser(usage)
    parser.add_option("-d", "--directory", dest="path",
                      help="picture directory (default: ./)")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help="make lots of noise [default]")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose",
                      help="be vewwy quiet (I'm hunting wabbits)")
    parser.set_defaults(verbose=True, path='./')
    (opt, args) = parser.parse_args()
    
    # input validation and interpretation
    if not args:
        parser.error("no command given")
    else:
        if not os.path.isdir(opt.path): parser.error("invalid directory: %s" % opt.path)
        # first argument is the command
        cmd = args.pop(0)
        for arg in args:
            if not os.path.isfile(arg):
                parser.error("invalid file: %s" % arg)
        else:
            files = set(os.path.realpath(arg) for arg in args)

    path = os.path.realpath(opt.path)
    cache_file = os.path.join(path, config.CACHE_FILE)
    try:
        # load cache file
        cache = shelve.open(cache_file, writeback=False)
        if opt.verbose:
            print "Using file %s as cache" % cache_file
        if cmd == "import":
            pics = import_dir(path, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        elif cmd == "list":
            pics = read_cache(cache, opt.verbose)
            list_pics(pics, opt.verbose)
        elif cmd == "clean":
            pics = read_cache(cache, opt.verbose)
            clean_dir(pics, cache_file, opt.verbose)
        elif cmd == "show":
            pics = read_cache(cache, opt.verbose)
            show_dir(pics, opt.verbose)
        elif cmd == "checksums":
            # TODO: add this to 'list' command with a checksum flag
            pics = read_cache(cache, opt.verbose)
            list_checksums(pics, opt.verbose)
        elif cmd == "check":
            pics = read_cache(cache, opt.verbose)
            check_dir(pics, opt.verbose)
        elif cmd == "delete":
            pics = read_cache(cache, opt.verbose)
            pics = delete_pics(path2pic(files, pics, opt.verbose), pics, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        elif cmd == "update":
            pics = read_cache(cache, opt.verbose)
            raise NotImplementedError
            update_dir(pics, path, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        else:
            parser.error("invalid argument: %s" % cmd)        
    finally:
        cache.close()
    

if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        print "Exiting."
        sys.exit(None)

