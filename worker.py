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

import sys
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
# FIXME: all write to writable picture attributes has to be thread safe
class Worker(threading.Thread):
    """Worker is a thread class who works on jobs coming from a queue.

    Constructor arguments:
        name (string)           :   unique identifier of worker
        pool                    :   object to which worker belongs (e.g. Stage)
        inqueue (Queue.Queue)   :   queue from which worker gets his jobs
        outqueue (Queue.Queue)  :   queue into which worker puts finished jobs
        logpath (string)        :   logfile path
    """

    name = 'Worker'

    def __init__(self, pool, inqueue, outqueue, logpath='./'):
        threading.Thread.__init__(self)
        self.pool = pool   
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.logpath = logpath
        
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
        self.outfile = self.logpath + '/' + self.name + '.log'
        self.outfile_handle=open(self.outfile, 'w')
        self.errfile = self.logpath + '/' + self.name + '.err'
        self.errfile_handle=open(self.errfile, 'w')
        
    def _end_logging(self):
        # Closing logging file handles    
        self.outfile_handle.close()
        self.errfile_handle.close()

    def run(self):
        self._init_logging()
        # Keep running as long as there are jobs in queue
        while self.pool.isactive:
            try:
                # get next queue item, block for WORKER_TIMEOUT seconds if empty
                (picture, jobnr) = self.inqueue.get(True, config.WORKER_TIMEOUT)
            except Queue.Empty:
                print self.name, ": Nothing more to do. Exiting..."
                break
            
            if self._work(picture, jobnr):   
                self.outqueue.put((picture, jobnr))
                # TODO: make history more useful: exact job performed, timestamp, etc.
                # FIXME: this has to be thread safe
                picture.history.append((self.name, time.ctime()))
                sidecar = self._compile_sidecar_path(picture)
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
        print self.name, "(", jobnr, "): ..."
        with open(picture.path, 'rb') as pic:
            buf = pic.read()
        digest = hashlib.sha1(buf).hexdigest()
        # TODO: no sidecar file needed?
        picture.checksum = digest
        
        # write digest to a sidecar file     
        (hash_file, content_type) = self._compile_sidecar_path(picture)
        with open(hash_file, 'w') as f:
            f.write(digest + '  ' + os.path.basename(picture.path) + '\n')    
        
        print self.name, "(", jobnr, "): Ok."

        # FIXME: Return something useful
        return True
        
    def _compile_sidecar_path(self, picture):
        path = picture.basename + '.sha1'
        content_type = 'Checksum'
        return (path, content_type)    


# TODO: check return code of subprocess
class SubprocessWorker(Worker):
    """SubprocessWorker class derived from Worker executes external programs."""
    
    name = 'SubprocessWorker'
    
    def _compile_command(self, picture):
        """
        Returns command to be executed together with working directory

        This function has to be overriden by derived classes.
            Arguments passed    : picture object
            Arguments returned  : tuple of strings (cmd, path)
        """
        
        pass    # Override me in derived class
        return (None, None)
    
    def _work(self, picture, jobnr):
        (cmd, path) = self._compile_command(picture)
        try:
            self.process = subprocess.Popen(cmd, shell=False, cwd=path,
                                            stdout=self.outfile_handle,
                                            stderr=self.errfile_handle)
            print self.name, "(", jobnr, "): ..."
            retcode = self.process.wait()
            if retcode < 0:
                print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", cmd, " terminated with signal", -retcode
            else:
                print self.name, "(", jobnr, "): Ok."
        except OSError, e:
            print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", cmd, " execution failed:", e
            
        # FIXME: Return something useful
        return True
        
        
class DCRawThumbWorker(SubprocessWorker):
    """
    DCRawThumbWorker is a subprocess worker that uses DCRaw to extract thumbnails.
    """
    
    name = 'DCRawThumbWorker'
    _bin = config.DCRAW_BIN
    _args = '-e'
    
    def _compile_command(self, picture):
        cmd = [ self._bin, self._args, picture.path ]
        path = os.path.dirname(picture.path)
        return (cmd, path)
        
    def _compile_sidecar_path(self, picture):
        path = picture.basename + '.thumb.jpg'
        content_type = 'Thumbnail'
        return (path, content_type)    


class Exiv2MetadataWorker(SubprocessWorker):
    """
    Exiv2MetadataWorker is a subprocess worker that uses Exiv2 to extract metadata.
    """
    
    name = 'Exiv2MetadataWorker'
    _bin = config.EXIV2_BIN
    _args = ['-e', 'X', 'ex']
    
    def _compile_command(self, picture):
        # FIXME: This is ugly
        cmd = [ self._bin ] + self._args + [ picture.path ]
        path = os.path.dirname(picture.path)
        return (cmd, path)
        
    def _compile_sidecar_path(self, picture):
        path = picture.basename + '.xmp'
        content_type = 'XMP Metadata'
        return (path, content_type)
        
        
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
        cmd = [ self._bin, self._args, picture.path ]
        path = os.path.dirname(picture.path)
        return (cmd, path)
    

                    
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

