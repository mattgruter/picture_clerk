#!/usr/bin/env python
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
    dirlist = os.listdir(path)
    files = fnmatch.filter(dirlist, "*.NEF")
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


def clean_dir(pics, cache_file, verbose):
    for pic in pics:
        print 'Removing all associated sidecar files of %s.' % pic.path
        for s in pic._sidecars:
            try:
                os.remove(s.path)
            except OSError:
                print 'Error: Unable to remove %s.' % s.path
                sys.exit(1)
    print 'Removing local cache file %s.' % cache_file
    try:
        os.remove(cache_file)
    except OSError:
        print 'Error: Unable to remove %s.' % cache_file
        sys.exit(1)


def show_dir(pics, verbose):
    if verbose:
        print 'Starting image viewer QIV...'
    args = [ 'qiv', '-mt']
    args.extend(pic.thumbnail for pic in pics)
    try:
        viewer_process = subprocess.Popen(args, shell=False)
        retcode = viewer_process.wait()
        #retcode = subprocess.call(args, shell=False)
        if retcode < 0:
            print >>sys.stderr, "Child was terminated by signal", -retcode
    except OSError, e:
        print >>sys.stderr, "Execution failed:", e
    
    
def list_checksums(pics, verbose):
    filenames = [pic.basename+pic.extension for pic in pics]
    checksums = [pic.checksum for pic in pics]
    # FIXME: ugly loop
    for (i, f) in enumerate(filenames):
        print '%s  %s' % (checksums[i], filenames[i])
    
    
def check_dir(pics, verbose):
    pass
    

def update_dir(pics, path, verbose):
    pass


def main():
    from optparse import OptionParser

    usage = "usage: %prog [OPTIONS] ARG1 ARG2"
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help="make lots of noise [default]")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose",
                      help="be vewwy quiet (I'm hunting wabbits)")
    parser.set_defaults(verbose=True)
    (opt, args) = parser.parse_args()
    
    # input validation and interpretation
    if not args:
        parser.error("incorrect number of arguments")
    (cmd, path) = (args[0], args[1])
    if not os.path.isdir(path):
        parser.error("invalid directory: %s" % path)
    cache_file = os.path.realpath(os.path.join(path, config.CACHE_FILE))
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
            raise NotImplementedError
            check_dir(pics, opt.verbose)
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

