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
import sys
import fnmatch
import shelve

from recipe import *
from worker import *
from pipeline import *
from picture import *
from config import *
from qivcontrol import *


class ProgressBar:
    # (c) by Randy Pargman, Wed, 11 Dec 2002
	def __init__(self, label='Progress', minValue = 0, maxValue=100, totalWidth=12):
		self.progBar = "[]"   # This holds the progress bar string
		self.label = label
		self.min = minValue
		self.max = maxValue
		self.span = maxValue - minValue
		self.width = totalWidth
		self.amount = 0       # When amount == max, we are 100% done 
		self.updateAmount(0)  # Build progress bar string

	def updateAmount(self, newAmount):
		if newAmount < self.min: newAmount = self.min
		if newAmount > self.max: newAmount = self.max
		self.amount = newAmount

		# Figure out the new percent done, round to an integer
		diffFromMin = float(self.amount - self.min)
		percentDone = (diffFromMin / float(self.span)) * 100.0
		percentDone = round(percentDone)
		percentDone = int(percentDone)

		# Figure out how many hash bars the percentage should be
		allFull = self.width - 2
		numHashes = (percentDone / 100.0) * allFull
		numHashes = int(round(numHashes))

		# build a progress bar with hashes and spaces
		self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

		# figure out where to put the percentage, roughly centered
		percentPlace = (len(self.progBar) / 2) - len(str(percentDone)) 
		percentString = str(percentDone) + "%"

		# slice the percentage into the bar
		self.progBar = self.label + ": " + self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

	def __str__(self):
		return str(self.progBar)


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
    import time
    # TODO: use os.walk to search for files recursively
    dirlist = os.listdir(path)
    # TODO: what files to import? check that only NEF files are present so that
    #       already present sidecar files are not overwritten. or maybe,
    #       analyze directory and add present sidecar files (=same basename) to
    #       picture instance.
    # TODO: check if cache file .pic.db is already present to avoid writing
    #       it over. even better: add new pictures to already present cache.
    files = fnmatch.filter(dirlist, config.IMPORT_FILE_PATTERN)
    if not files:
        if verbose:
            print 'No picture files found. Exiting.'
        return
    # create Picture instances and place them in a set to avoid duplicates
    pics = set([ Picture(f) for f in files ])
    # pipeline instructions: retrieve metadata & thumbnail, calculate checksum, rotate thumbnails
    instructions = [HashDigestWorker, MetadataWorker, Exiv2XMPSidecarWorker,
                    DCRawThumbWorker, AutorotWorker]
    recipe = Recipe(instructions)

    if config.LOGGING:
        # create logfile directory if it doesn't exist yet
        if not os.path.isdir(os.path.join(path, config.LOGDIR)):
            try:
                os.mkdir(os.path.join(path, config.LOGDIR))
            except OSError:
                print >>sys.stderr, 'Not possible to create log directory. Disabling logging.'
                logdir = None
            else:
                logdir = config.LOGDIR
    else:
        logdir = None
    # pipeline environment variables
    environ = dict(path=path, logdir=logdir)

    pl = Pipeline('Pipeline1', recipe, **environ)
    for pic in pics:
        pl.put(pic)
    pl.start()

    if verbose:
        progress = 0
        # TODO: show progress of each stage
#        progBars = [ProgressBar(stage.name, 0, len(pics), 30) for stage in pl.stages]        
        progBar = ProgressBar(minValue=0, maxValue=len(pics), totalWidth=30)
        while True:
            tmpProgress = pl.get_progress()
            if tmpProgress != progress:
                progress = tmpProgress
                if progress >= len(pics):
                    break   # Exit; all pictures were processed
                else:
                    progress = tmpProgress
                    progBar.updateAmount(progress)
                    sys.stdout.write(str(progBar) + '\r')
                    sys.stdout.flush()
            time.sleep(0.1)
        # Finish progress display: show 100% and return to normal output
        progBar.updateAmount(len(pics))
        sys.stdout.write(str(progBar) + '\r')
        sys.stdout.flush()
        print
    # Make sure that all worker threads have terminated
    pl.join()
    return pics
    

def list_pics(pics, verbose):
    for pic in sorted(pics):
        print pic
        
        
def path2pic(files, pics, verbose):
    res = []
    for pic in pics:
        # look in all associated files and the picture basename for a match
        for fname in pic.get_filenames() + [pic.basename]:
            if fname in files:
                res.append(pic)
    return res
#    return [pic for pic in pics if pic. in files]
    
        
def clean_pics(pics, path, verbose):
    for pic in pics:
        if verbose:
            print 'Removing all associated sidecar files of %s.' % pic.filename
        for s in pic._sidecars:
            try:
                os.remove(os.path.join(path, s.filename))
            except OSError:
                # FIXME: shouldn't fail if file is not present (we just don't
                #        care then), but it should fail if we can't remove the
                #        file due to wrong permissions.
                print 'Error: Unable to remove sidecar file %s.' % s.filename
                sys.exit(1)
        pic._sidecars = []
    return pics


def clean_dir(pics, path, verbose):
    # cleaning pictures
    clean_pics(pics, path, verbose)
    
    # removing log files
    _logDir = os.path.join(path, config.LOGDIR)
    if verbose:
        print 'Removing log files in %s.' % _logDir
    try:
        delete_tree(_logDir)
    except OSError:
        print 'Error: Unable to remove log files in %s' % _logDir
        sys.exit(1)
        
    # removing cache file
    _cacheFile = os.path.join(path, config.CACHE_FILE)
    if verbose:
        print 'Removing local cache file %s.' % _cacheFile
    try:
        os.remove(_cacheFile)
    except OSError:
        print 'Error: Unable to remove cache file %s.' % _cacheFile
        sys.exit(1)
    
    
def delete_pics(selection, pics, path, verbose):
    clean_pics(selection, path, verbose)
    for pic in selection:
        if verbose:
            print 'Removing %s.' % pic.filename
        try:
            pics.remove(pic)
            os.remove(os.path.join(path, pic.filename))
        except KeyError, OSError:
            print 'Error: Unable to remove %s.' % s.path
            sys.exit(1)    
    return pics
    
    
def delete_tree(root):
    """
    Delete a directory tree
    """
    for path, dirs, files in os.walk(root, topdown=False):
        for fname in files:
            os.remove(os.path.join(path, fname))
        for dname in dirs:
            os.rmdir(os.path.join(path, dname))
    os.rmdir(root)
        

def show_dir(pics, path, verbose):
    import time
    if verbose:
        print 'Starting image viewer QIV...'
    qivCtrl = QivController('qiv', ['-m', 't'], pics, path)
    qivCtrl.start()
    qivCtrl.join()
    if verbose:
        print 'QIV exited.'
    # TODO: QivController should return a list of Picture references instead of
    #       a list of thumbnail files in trash (path2pic within QivController?)
    trashContent = path2pic(qivCtrl.getTrashContent(), pics, verbose)
    trashPath = qivCtrl.getTrashPath()
    if trashContent:
        print 'Deleted pictures:'
        for pic in trashContent:
            print '  %s' % pic.filename
            # move deleted thumbnails back into original directory
            os.rename(os.path.join(trashPath, pic.thumbnail), os.path.join(path, pic.thumbnail))
        os.rmdir(trashPath)
        delChoice = raw_input('Do you want to permanently delete above pictures [yN]: ')
        if delChoice == 'y' or delChoice == 'Y':
            pics = delete_pics(trashContent, pics, path, verbose)
    return pics
    
    
def list_checksums(pics, verbose):
    output = ('%s *%s' % (p.checksum, p.basename+p.extension) for p in sorted(pics))
    for line in output:
        print line
    
    
def check_dir(pics, path, verbose):
    # TODO: use worker threads to check checksums
    import hashlib
    for pic in sorted(pics):
        try:
            with open(os.path.join(path, pic.filename), 'rb') as pic_file:
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
        # FIXME: arguments don't necessarily need to be valid files/paths
#        for arg in args:
#            if not os.path.isfile(arg):
#                parser.error("invalid file: %s" % arg)
#            elif not os.path.samefile(os.path.dirname(arg), opt.path):
#                parser.error("file $s outside directory $s" % (arg, opt.path))
#        else:
#            files = set(os.path.basename(arg) for arg in args)
        files = set(os.path.basename(arg) for arg in args)

    _cacheFile = os.path.join(opt.path, config.CACHE_FILE)
    try:
        # load cache file
        # TODO: use different cache format that is fully protable and possibly
        #       text based and human readable (i.e. json?)
        cache = shelve.open(_cacheFile, writeback=False)
        if opt.verbose:
            print "Using file %s as cache" % _cacheFile
        if cmd == "import":
            pics = import_dir(opt.path, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        elif cmd == "list":
            pics = read_cache(cache, opt.verbose)
            list_pics(pics, opt.verbose)
        elif cmd == "clean":
            pics = read_cache(cache, opt.verbose)
            clean_dir(pics, opt.path, opt.verbose)
        elif cmd == "show":
            pics = read_cache(cache, opt.verbose)
            pics = show_dir(pics, opt.path, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        elif cmd == "checksums":
            # TODO: add this to 'list' command with a checksum flag
            pics = read_cache(cache, opt.verbose)
            list_checksums(pics, opt.verbose)
        elif cmd == "check":
            pics = read_cache(cache, opt.verbose)
            check_dir(pics, opt.path, opt.verbose)
        elif cmd == "delete":
            pics = read_cache(cache, opt.verbose)
            pics = delete_pics(path2pic(files, pics, opt.verbose), pics, opt.path, opt.verbose)
            write_cache(cache, pics, opt.verbose)
        elif cmd == "update":
            pics = read_cache(cache, opt.verbose)
            raise NotImplementedError
            update_dir(pics, opt.path, opt.verbose)
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

