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
import shutil
import paramiko
try:
   import cPickle as pickle
except:
   import pickle

from recipe import *
from worker import *
from pipeline import *
from picture import *
from config import *
from qivcontrol import *
from path import *


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


def init_repo(path):
    """
    Initializes a directory as a PictureClerk repsoitory.
    """
    
    # TODO: handle remote paths
    
    pic_dir = os.path.join(path, config.PIC_DIR)
    try:
        os.mkdir(pic_dir)
    except OSError as err:
        print "Unable to initialize directory %s (%s)" % (path, err)
        sys.exit(1)


def import_dir(path, verbose):
    import time
    
    init_repo(path)
    
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
        
    # create Picture instances and place them in a set to avoid duplicates
    pics = set([ Picture(f) for f in files ])
    # pipeline instructions: retrieve metadata & thumbnail, calculate checksum, rotate thumbnails
    instructions = [HashDigestWorker, Exiv2XMPSidecarWorker,
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
        
        
def path2pic(path, pics):
    """
    Return picture object that has the given path in its file list.
    
    path2pic searches among the original picture filename, all sidecar filenames
    and the picture basename.
    """
    for pic in pics:
        if path in pic.get_filenames() + [pic.basename]:
            return pic
    
        
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
        
    # removing PictureClerk directory and its contents
    pic_dir = os.path.join(path, config.PIC_DIR)
    try:
        delete_tree(pic_dir)
    except OSError as err:
        print "Unable to remove %s (Error: %s)" % (pic_dir, err)
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
    trashContent = [path2pic(pic_path, pics) for pic_path in qivCtrl.getTrashContent()]
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
    raise NotImplementedError


def clone_dir(pics, src_path, dest_path, thumbs, link=False):

    # TODO: handle remote dest_paths (how to init repo remotly?)
    # TODO: save path of origin (src_path)
    # TODO: draw progress bar

    if dest_path.isremote:
        print "Cloning to remote paths not supported yet."
        raise NotImplementedError
        
    init_repo(dest_path.path)

    if src_path.islocal:
        if link:
            # create unix symlinks if linksonly is true
            copy = os.symlink
        else:
            # use shutil copy (aka 'cp -p' to copy files)
            copy = shutil.copy2
    elif src_path.protocol == "ssh":
            src_ssh = paramiko.SSHClient()
            # TODO: make sure that this is portable
            src_ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
            src_ssh.connect(src_path.hostname, username=src_path.username)
            src_sftp = src_ssh.open_sftp()
            copy = src_sftp.get
    
    for pic in pics:
        # FIXME: which thumbnail to copy? Now only last thumbnail is copied
        if thumbs:
            fnames = [pic.get_thumbnails()[-1].filename]
        else:
            fnames = pic.get_filenames()
        for fname in fnames:
            src = os.path.join(src_path.path, fname)
            dest = os.path.join(dest_path.path, fname)
            copy(src, dest)
            
    if src_path.protocol == "ssh":
        src_sftp.close()
        src_ssh.close()


def load_index(path):
    """
    Retrieve index of pictures from file.
    """
    
    # TODO: use different index format that is fully protable and possibly
    #       text based and human readable (i.e. json, xml?)
    index_path = os.path.join(path.path, config.INDEX_FILE)
    mode = 'rb'
    if path.islocal:
        try:
            index_fh = open(index_path, mode)
        except IOError as err:
            print "Error accessing %s: %s" % (index_path, err)
            sys.exit(2)
    elif path.protocol == "ssh":
            ssh = paramiko.SSHClient()
            # TODO: make sure that this is portable
            ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
            ssh.connect(path.hostname, username=path.username)
            sftp = ssh.open_sftp()
            index_fh = sftp.file(index_path, mode)
    else:
        print "%s:// paths are not supported." % path.protocol
        sys.exit(2)
#    logging.debug("Loading from index file %s" % index_path)
    try:
        index = pickle.load(index_fh)
    except pickle.UnpicklingError as err:
        print "Error reading from %s: %s" % (index_path, err)
    finally:
        # TODO: this finally clause should come from a more global try statement
        #       that covers the block from where index_fh is created
        index_fh.close()
        if path.protocol == "ssh":
            sftp.close()
            ssh.close()

    return index
    
    
def write_index(path, index):
    """
    Write index of pictures to file.
    """
    
    index_path = os.path.join(path.path, config.INDEX_FILE)
    mode = 'wb'
    if path.islocal:
        try:
            index_fh = open(index_path, mode)
        except IOError as err:
            print "Error accessing %s: %s" % (index_path, err)
            sys.exit(2)
    elif path.protocol == "ssh":
            ssh = paramiko.SSHClient()
            # TODO: make sure that this is portable
            ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
            ssh.connect(path.hostname, username=path.username)
            sftp = ssh.open_sftp()
            index_fh = sftp.file(index_path, mode)
    else:
        print "%s:// paths are not supported." % path.protocol
        sys.exit(2)
#    logging.debug("Writing to index file %s" % index_path)
    try:
        index = pickle.dump(index, index_fh)
    except pickle.PicklingError as err:
        print "Error writing to %s: %s" % (index_path, err)
    finally:
        # TODO: this finally clause should come from a more global try statement
        #       that covers the block from where index_fh is created
        index_fh.close()
        if path.protocol == "ssh":
            sftp.close()
            ssh.close()


def main():
    from optparse import OptionParser, OptionGroup
    
    # TODO: supply command to convert repositories with old cache format to
    #       repositories with new index format

    usage = "Usage: %prog [OPTIONS] import\n" \
          + "   or: %prog [OPTIONS] update\n" \
          + "   or: %prog [OPTIONS] clone SRC\n" \
          + "   or: %prog [OPTIONS] list\n" \
          + "   or: %prog [OPTIONS] show\n" \
          + "   or: %prog [OPTIONS] check\n" \
          + "   or: %prog [OPTIONS] delete FILES"
                    
    parser = OptionParser(usage)
    
    # Global options
    parser.add_option("-d", "--directory", dest="path",
                           help="picture directory (default: %default)")
    # TODO: use logging package
    parser.add_option("-v", "--verbose",
                           action="store_true", dest="verbose",
                           help="make lots of noise [default]")
    parser.add_option("-q", "--quiet",
                           action="store_false", dest="verbose",
                           help="be vewwy quiet (I'm hunting wabbits)")
                           
    # Options for the 'clone' command
    clone_opts = OptionGroup(parser, "Clone options",
                             "Options for the clone command.")
    clone_opts.add_option("-t", "--thumbs",
                          action="store_true", dest="thumbs",
                          help="clone only thumbnail files")
    clone_opts.add_option("-l", "--link",
                          action="store_true", dest="link",
                          help="link instead of copying during cloning")
    parser.add_option_group(clone_opts)

    parser.set_defaults(verbose=True, path='.')
    (opt, args) = parser.parse_args()
    
    # input validation and interpretation
    if not args:
        parser.error("no command given")

    path = Path.fromPath(opt.path)
    if path.islocal and not path.exists():
        parser.error("invalid directory: %s" % path)
        
    # first argument is the command
    cmd = args.pop(0)

    if cmd == "import":
        # TODO: handle remote paths
        pics = import_dir(path.path, opt.verbose)
        write_index(path, pics)
    elif cmd == "list":
        pics = load_index(path)
        list_pics(pics, opt.verbose)
    elif cmd == "clean":
        pics = load_index(path)
        # TODO: handle remote paths
        clean_dir(pics, path.path, opt.verbose)
    elif cmd == "show":
        pics = load_index(path)
        if path.isremote:
            print "Only local repositories are supported for viewing."
            sys.exit(1)
        new_pics = show_dir(pics, path.path, opt.verbose)
        # TODO: only update index if new_pics is not the same as pics
        write_index(path, new_pics)
    elif cmd == "checksums":
        # TODO: add this to 'list' command with a checksum flag
        pics = load_index(path)
        list_checksums(pics, opt.verbose)
    elif cmd == "check":
        pics = load_index(path)
        # TODO: handle remote paths
        check_dir(pics, path.path, opt.verbose)
    elif cmd == "delete":
        pics = load_index(path)
        files = args
        pics_to_remove = [path2pic(pic_path, pics) for pic_path in files]
        # TODO: handle remote paths
        pics = delete_pics(pics_to_remove, pics, path.path, opt.verbose)            
        write_index(path, pics)
    elif cmd == "update":
        # FIXME: import is a special case of update
        # TODO: maybe call this command sync?
        pics = load_index(path)
        # TODO: handle remote paths
        new_pics = update_dir(pics, opt.path, opt.verbose)
        # TODO: only update index if new_pics is not the same as pics
        write_index(path, new_pics)
    elif cmd == "clone":
        src_path = Path.fromPath(args.pop(0))
        if src_path.islocal and not src_path.exists():
            parser.error("invalid directory: %s" % src_path)
        pics = load_index(src_path)
        clone_dir(pics, src_path, path, opt.thumbs, opt.link)
        write_index(path, pics)
    else:
        parser.error("invalid argument: %s" % cmd)

    

if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        # FIXME: kill threads, wait for them and then exit
        print "Exiting."
        sys.exit(None)

