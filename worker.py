from __future__ import with_statement
"""worker.py

PictureClerk - The little helper for your picture workflow.
This file contains the Worker class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"

import os
import threading
import Queue
import subprocess
import time
import hashlib
import pyexiv2

import config


#class WorkerState():
#    IDLE = 0    # worker is waiting for jobs
#    BUSY = 1    # worker is processing a job


# TODO: error/execption handling in thread class or outside?
# TODO: unit tests
# TODO: queue_timeout should be controlled by stage or pipleine resp. workertype
# TODO: implement batch workers: they take several pictures from a queue and
#       process in the same run due to better efficiency (typically subprocess
#       workers to circumvent large process starting overhead).
# TODO: _compile_sidecar_path in Worker and _compile_command in Subprocess class
#       should return dictionaries insteaf of tuples
# FIXME: all write to writable picture attributes has to be thread safe
class Worker(threading.Thread):
    """
    Worker is a thread class who works on jobs coming from a queue.

    Constructor arguments:
        name (string)           :   unique identifier of worker
        inqueue (Queue.Queue)   :   queue from which worker gets his jobs
        outqueue (Queue.Queue)  :   queue into which worker puts finished jobs
        pool                    :   object to which worker belongs (i.e. Stage)
        path (string)           :   path in which the worker is to base its work
        logpath (string)        :   logfile path
    """

    name = 'Worker'

    def __init__(self, inqueue, outqueue, number, pool, path, logdir):
        threading.Thread.__init__(self)
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.number = number
        self.pool = pool
        self.path = path
        if logdir:
            self.logging = True
            self.logdir = logdir
        else:
            self.logging = False
        
    def _work(self, picture, jobnr):
        pass    # Override me in derived class
        return False
        
    def _compile_sidecar_path(self, picture):
        """
        Returns path and content type of generated sidecar file by the worker
        
        This function has to be overriden by derived class if sidecar files are
        generated.
            Arguments passed    : picture object
            Arguments returned  : tuple of strings (path, content_type)
        """
        
        pass    # Override me in derived class
        return None
        
    def _init_logging(self):
        if self.logging:
            _logfile = os.path.join(self.path, self.logdir, self.name + str(self.number) + '.log')
            self.outlog_handle=open(_logfile, 'w', 0)   # unbuffered
            _errfile = os.path.join(self.path, self.logdir, self.name + str(self.number) + '.err')
            self.errlog_handle=open(_errfile, 'w', 0)   # unbuffered
        else:
            self.outlog_handle = None
            self.errlog_handle = None
        
    def _end_logging(self):
        # Closing logging file handles    
        self.outlog_handle.close()
        self.errlog_handle.close()

    def run(self):
        self._init_logging()
        if self.logging: print >>self.outlog_handle, 'Starting up...'
        
        try:
            while True:
                self.pool.wakeSignal.wait()
                if not self.pool.isactive:
                    if self.logging: print >>self.outlog_handle, 'Terminating. Bye bye.'
                    break
                try:
                    # get next queue item, block for WORKER_TIMEOUT seconds if empty
                    (picture, jobnr) = self.inqueue.get(True, config.WORKER_TIMEOUT)
                except Queue.Empty:
                    pass    # try again
                    
                else:
                    if self.logging: print >>self.outlog_handle, 'Loading %s...' % picture.filename
                    if self._work(picture, jobnr):   
                        self.outqueue.put((picture, jobnr))
                        if self.logging: print >>self.outlog_handle, 'DONE %s' % picture.filename
                        # TODO: make history more useful: exact job performed, timestamp, etc.
                        # FIXME: this has to be thread safe (it is now because a
                        #        every picture is worked on by only one worker but if
                        #        we introduce parallel stages or piplines then we have
                        #        to fix this.)
                        picture.history.append((self.name, time.ctime()))
                        sidecar = self._compile_sidecar_path(picture)
                        if sidecar:
                            picture.add_sidecar(*sidecar)
                        self.inqueue.task_done()
                    else:
                        raise(Exception('Worker failed to complete job'))
        finally:
            # ensure that _end_logging method is always called
            if self.logging: self._end_logging()
            
     
class ThumbWorker(Worker):
    """
    ThumbWorker extracts the thumbnail/preview file from a raw image file with
    help of pyexiv2.
    """
    
    name = 'ThumbWorker'
    
    def _work(self, picture, jobnr):
        
        metadata = pyexiv2.ImageMetadata(picture.filename)
        metadata.read()
        # pyexiv2 sorts previews by dimensions (ascending), we are only
        # interested in the one with the largest dimensions
        thumb = metadata.previews[-1]
        thumb_filename = picture.basename + '.thumb' + thumb.extension
        thumb_path = os.path.join(config.THUMB_SIDECAR_DIR, thumb_filename)
        # TODO: save MIME type
#        thumb_mime_type = thumb.mime_type
        try:
            thumb_fh = open(thumb_path, 'wb')
        except IOError:
            # TODO
            return False
        else:
            with thumb_fh:
                thumb_fh.write(thumb.data)
            return True
            
    def _compile_sidecar_path(self, picture):
        # FIXME: thumb might have different extension than "jpg", see above's
        #        use of pyexiv2's preview object: "... + thum.extension"
        #        sidecar_path should be determined in _work method and somehow
        #        returned by it.
        _filename = picture.basename + '.thumb.jpg'
        _path = os.path.join(config.THUMB_SIDECAR_DIR, _filename)
        _content_type = 'Thumbnail'
        return (_path, _content_type)    
     
            
class MetadataWorker(Worker):
    """
    MetadataWorker extracts metadata from an image and stores values of
    interest in a dictionary of the picture instance.
    """
    
    # FIXME: pyexiv2 doesn't seem to be thread safe...
    
    name = 'MetadataWorker'
    
    def _parse_exif(self, tag, value):
        # TODO: use eval to get to a human-readable value
#        return str(value)

        if isinstance(value, pyexiv2.Rational):
            # TODO: convert rational numbers to more sane values (rat, int?)
            return value
        else:
            if tag == 'Exif.Photo.ExposureProgram':
                # TODO: how to decode to a meaningful string?
                return value
            elif tag == 'Exif.Photo.MeteringMode':
                # TODO: how to decode to a meaningful string?
                return value
            elif tag == 'Exif.Photo.Flash':
                # TODO: how to decode to a meaningful string?
                return value
            elif tag == 'Exif.Photo.LightSource':
                # TODO: how to decode to a meaningful string?
                return value
            else:
                return value
            
    def _work(self, picture, jobnr):
        # TODO: catch exceptions of not accessible files
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): ..."
        _picFname = os.path.join(self.path, picture.filename)
        _keys = ['Exif.Photo.ExposureTime', 'Exif.Photo.FNumber',
                 'Exif.Photo.ExposureProgram', 'Exif.Photo.ISOSpeedRatings',
                 'Exif.Photo.DateTimeOriginal', 'Exif.Photo.DateTimeDigitized',
                 'Exif.Photo.ExposureBiasValue', 'Exif.Photo.MaxApertureValue',
                 'Exif.Photo.MeteringMode', 'Exif.Photo.WhiteBalance',
                 'Exif.Photo.Flash', 'Exif.Photo.LightSource',
                 'Exif.Photo.FocalLength', 'Exif.Photo.FocalLengthIn35mmFilm',
                 'Exif.Image.Make', 'Exif.Image.Model',
                 'Exif.Photo.UserComment']
        try:
            metadata = pyexiv2.ImageMetadata(_picFname)
            metadata.read()
            metadata.cacheAllExifTags()
        except IOError:
            # How should this be handled?
            print 'File not found: %s' % _picFname
        # TODO: better way to copy part of a dictionary?
        for k in _keys:
            try:
                picture.metadata[k] = self._parse_exif(k, metadata[k])
            except IndexError:
                picture.metadata[k] = None
            except IOError:
                picture.metadata[k] = None
                
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): Ok."

        # FIXME: Return something useful
        return True
            

class HashDigestWorker(Worker):
    """
    HashDigestWorker class derived from Worker calculates hash digests of
    picture files.
    """
    
    name = 'HashDigestWorker'
    
    def _work(self, picture, jobnr):
        # TODO: catch exceptions of not accessible files
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): ..."
        with open(os.path.join(self.path, picture.filename), 'rb') as pic:
            buf = pic.read()
        digest = hashlib.sha1(buf).hexdigest()
        picture.checksum = digest
        if config.SHA1_SIDECAR_ENABLED:
            # write digest to a sidecar file     
            (hashfile_path, contentType) = self._compile_sidecar_path(picture)
            hashfile_path = os.path.join(self.path, hashfile_path)
            try:
                with open(hashfile_path, 'w') as f:
                    f.write(digest + ' *' + picture.filename + '\n')
            except IOError as err:
                if self.logging:
                    print >>self.errlog_handle, self.name, "(", jobnr, "): ", \
                        "ERROR - error writing to file ", hashfile_path, \
                        "(", err, ")"
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): Ok."

        # FIXME: Return something useful
        return True
        
    def _compile_sidecar_path(self, picture):
        _filename = picture.basename + '.sha1'
        _path = os.path.join(config.SHA1_SIDECAR_DIR, _filename)
        _contentType = 'Checksum'
        return (_path, _contentType)    


# TODO: check return code of subprocess
class SubprocessWorker(Worker):
    """
    SubprocessWorker class derived from Worker executes external programs.
    """
    
    name = 'SubprocessWorker'
    
    def _compile_commands(self, picture):
        """
        Returns command to be executed together with working directory

        This function has to be overriden by derived classes.
            Arguments passed    : picture object
            Arguments returned  : command line (list of strings)
        """
        
        pass    # Override me in derived class
        return None
    
    def _work(self, picture, jobnr):
        commands = self._compile_commands(picture)
        
        for command in commands:
            try:
                # FIXME: use Python's logging facility (thread-safe)
                self.process = subprocess.Popen(command, shell=False, cwd=self.path,
                                                stdout=self.outlog_handle,
                                                stderr=self.errlog_handle)
                                                
#                # TODO: fix logging to file
#                print self.name, "(", jobnr, "): ..."
                retcode = self.process.wait()
                if retcode < 0:
                    if self.logging: print >>self.errlog_handle, self.name, "(", jobnr, "): ERROR - ", command, " terminated with signal", -retcode
                else:
#                    # TODO: fix logging to file
#                    print self.name, "(", jobnr, "): Ok."
                    pass
            except OSError, e:
                if self.logging: print >>self.errlog_handle, self.name, "(", jobnr, "): ERROR - ", command, " execution failed:", e
            
        # FIXME: Return something useful
        return True
        
        
class DCRawThumbWorker(SubprocessWorker):
    """
    DCRawThumbWorker is a subprocess worker that uses DCRaw to extract
    a thumbnail to a sidecar file.
    """
    
    name = 'DCRawThumbWorker'
    _bin = config.DCRAW_BIN
    _args = '-e'
    
    def _compile_commands(self, picture):
        cmd1 = [ self._bin, self._args, picture.filename ]
#        cmd2 = [ "mv", os.path.basename]
#        return cmd1, cmd2
        return cmd1, 
        
    def _compile_sidecar_path(self, picture):
        _filename = picture.basename + '.thumb.jpg'
        _path = os.path.join(config.THUMB_SIDECAR_DIR, _filename)
        _content_type = 'Thumbnail'
        return (_path, _content_type)    


class Exiv2XMPSidecarWorker(SubprocessWorker):
    """
    Exiv2XMPSidecarWorker is a subprocess worker that uses Exiv2 to extract
    metadata to a sidecar XMP file.
    """
    
    name = 'Exiv2XMPSidecarWorker'
    _bin = config.EXIV2_BIN
    _args = ['-e', 'X', 'ex']
    
    def _compile_commands(self, picture):
        cmd = [ self._bin ] + self._args + [ picture.filename ]
        return cmd,
        
    def _compile_sidecar_path(self, picture):
        _filename = picture.basename + '.xmp'
        _path = os.path.join(config.XMP_SIDECAR_DIR, _filename)
        _content_type = 'XMP Metadata'
        return (_path, _content_type)
       
       
class AutorotWorker(SubprocessWorker):
    """
    AutorotWorker is a subprocess worker using the jhead tool to automatically
    rotate thumbnails according to their EXIF header.
    """
    
    name = 'AutorotWorker'
    _bin = config.JHEAD_BIN
    _args = '-autorot'
    
    def _compile_commands(self, picture):
        cmd = [ self._bin, self._args, picture.thumbnail ]
        print cmd
        return cmd,

        
class GitAddWorker(SubprocessWorker):
    """
    GitAddWorker adds pictures to a git repository
    """
    
    # FIXME: Only one git instance can work on repository -> git repo lock.
    # TODO: Git would be many times faster if it worked on several pictures at once.
    
    name = 'GitAddWorker'
    _bin = config.GIT_BIN
    _args = 'add'
    
    def _compile_commands(self, picture):
        cmd = [ self._bin, self._args, picture.filename ]
        return cmd,
    
                    
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

