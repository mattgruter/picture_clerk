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
# TODO: _compile_sidecar_filename in Worker and _compile_command in Subprocess class
#       should return dictionaries insteaf of tuples
# FIXME: all write to writable picture attributes has to be thread safe
class Worker(threading.Thread):
    """Worker is a thread class who works on jobs coming from a queue.

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
        self.logdir = logdir
        
    def _work(self, picture, jobnr):
        pass    # Override me in derived class
        return False
        
    def _compile_sidecar_filename(self, picture):
        """
        Returns filename and content type of generated sidecar file by the worker
        
        This function has to be overriden by derived class if sidecar files are
        generated.
            Arguments passed    : picture object
            Arguments returned  : tuple of strings (filename, content_type)
        """
        
        pass    # Override me in derived class
        return None
        
    def _init_logging(self):
        _logfile = os.path.join(self.path, self.logdir, self.name + str(self.number) + '.log')
        self.outlog_handle=open(_logfile, 'w')   # unbuffered
        _errfile = os.path.join(self.path, self.logdir, self.name + str(self.number) + '.err')
        self.errlog_handle=open(_errfile, 'w')   # unbuffered
        
    def _end_logging(self):
        # Closing logging file handles    
        self.outlog_handle.close()
        self.errlog_handle.close()

    def run(self):
        self._init_logging()
        # Keep running as long as there are jobs in queue
        while self.pool.isactive:
            try:
                # get next queue item, block for WORKER_TIMEOUT seconds if empty
                (picture, jobnr) = self.inqueue.get(True, config.WORKER_TIMEOUT)
            except Queue.Empty:
                # TODO: should threads really exit on their own or should some
                # sort of dispatcher terminate them as soon as they are not
                # needed anymore (i.e. no more jobs left)? Propably yes.
                # TODO: fix logging to file
#                print self.name, ": Nothing more to do. Exiting..."
                break
            
            if self._work(picture, jobnr):   
                self.outqueue.put((picture, jobnr))
                # TODO: make history more useful: exact job performed, timestamp, etc.
                # FIXME: this has to be thread safe
                picture.history.append((self.name, time.ctime()))
                sidecar = self._compile_sidecar_filename(picture)
                if sidecar:
                    picture.add_sidecar(*sidecar)
                self.inqueue.task_done()
            else:
                raise(Exception('Worker failed to complete job'))
        self._end_logging()
            

class HashDigestWorker(Worker):
    """HashDigestWorker class derived from Worker calculates hash digests of picture files."""
    
    name = 'HashDigestWorker'
    
    def _work(self, picture, jobnr):
        # TODO: catch exceptions of not accessible files
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): ..."
        with open(os.path.join(self.path, picture.filename), 'rb') as pic:
            buf = pic.read()
        digest = hashlib.sha1(buf).hexdigest()
        # TODO: no sidecar file needed?
        picture.checksum = digest
        
        # write digest to a sidecar file     
        (hashFilename, contentType) = self._compile_sidecar_filename(picture)
        with open(os.path.join(self.path, hashFilename), 'w') as f:
            f.write(digest + '  ' + picture.filename + '\n')    
        # TODO: fix logging to file
#        print self.name, "(", jobnr, "): Ok."

        # FIXME: Return something useful
        return True
        
    def _compile_sidecar_filename(self, picture):
        _filename = picture.basename + '.sha1'
        _contentType = 'Checksum'
        return (_filename, _contentType)    


# TODO: check return code of subprocess
class SubprocessWorker(Worker):
    """SubprocessWorker class derived from Worker executes external programs."""
    
    name = 'SubprocessWorker'
    
    def _compile_command(self, picture):
        """
        Returns command to be executed together with working directory

        This function has to be overriden by derived classes.
            Arguments passed    : picture object
            Arguments returned  : command line (list of strings)
        """
        
        pass    # Override me in derived class
        return None
    
    def _work(self, picture, jobnr):
        command = self._compile_command(picture)
        try:
            self.process = subprocess.Popen(command, shell=False, cwd=self.path,
                                            stdout=self.outlog_handle,
                                            stderr=self.errlog_handle)
            # TODO: fix logging to file
#            print self.name, "(", jobnr, "): ..."
            retcode = self.process.wait()
            if retcode < 0:
                print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", command['cmd'], " terminated with signal", -retcode
            else:
                # TODO: fix logging to file
#                print self.name, "(", jobnr, "): Ok."
                pass
        except OSError, e:
            print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", command['cmd'], " execution failed:", e
            
        # FIXME: Return something useful
        return True
        
        
class DCRawThumbWorker(SubprocessWorker):
    """
    DCRawThumbWorker is a subprocess worker that uses DCRaw to extract thumbnails.
    """
    
    #TODO: autorot thumbnail pictures
    
    name = 'DCRawThumbWorker'
    _bin = config.DCRAW_BIN
    _args = '-e'
    
    def _compile_command(self, picture):
        return [ self._bin, self._args, picture.filename ]
        
    def _compile_sidecar_filename(self, picture):
        _filename = picture.basename + '.thumb.jpg'
        _content_type = 'Thumbnail'
        return (_filename, _content_type)    


class Exiv2MetadataWorker(SubprocessWorker):
    """
    Exiv2MetadataWorker is a subprocess worker that uses Exiv2 to extract metadata.
    """
    
    name = 'Exiv2MetadataWorker'
    _bin = config.EXIV2_BIN
    _args = ['-e', 'X', 'ex']
    
    def _compile_command(self, picture):
        return [ self._bin ] + self._args + [ picture.filename ]
        
    def _compile_sidecar_filename(self, picture):
        _filename = picture.basename + '.xmp'
        _content_type = 'XMP Metadata'
        return (_filename, _content_type)
       
       
class AutorotWorker(SubprocessWorker):
    """
    AutorotWorker is a subprocess worker using the jhead tool to automatically
    rotate thumbnails according to their EXIF header.
    """
    
    name = 'AutorotWorker'
    _bin = config.JHEAD_BIN
    _args = '-autorot'
    
    def _compile_command(self, picture):
        return [ self._bin, self._args, picture.thumbnail ]

        
class GitAddWorker(SubprocessWorker):
    """
    GitAddWorker adds pictures to a git repository
    """
    
    # FIXME: Only one git instance can work on repository -> git repo lock.
    # TODO: Git would be many times faster if it worked on several pictures at once.
    
    name = 'GitAddWorker'
    _bin = config.GIT_BIN
    _args = 'add'
    
    def _compile_command(self, picture):
        return [ self._bin, self._args, picture.filename ]
    
                    
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

