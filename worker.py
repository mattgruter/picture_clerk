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
import threading
import Queue
import subprocess


# Time in seconds to wait before Worker exits when its queue is empty
_QUEUE_TIMEOUT = 3


#class WorkerState():
#    IDLE = 0    # worker is waiting for jobs
#    BUSY = 1    # worker is processing a job


# TODO: error/execption handling in thread class or outside?
# TODO: unit tests
# TODO: queue_timeout should be controlled by stage or pipleine resp. workertype
class Worker(threading.Thread):
    """Worker is a thread class who works on jobs coming from a queue.

    Constructor arguments:
        name (string)       :   unique identifier of worker
        seq_num (int)       :   sequence number of worker inside a pipeline
        path (string)       :   filesystem path in which the worker should conduct his work
        queue (Queue.Queue) :   queue from which worker gets his jobs.
        descr (string)      :   descriptive text for logging and such
    
    Unit tests:    
    >>> Worker('test', './', 'no-queue', 'Unit testing the Worker class')
    <Worker(Thread-1, initial)>
    """

    def __init__(self, name, pool, inqueue, outqueue, logpath='./'):
        threading.Thread.__init__(self)
        self.name = name     
        self.pool = pool   
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.logpath = logpath
        
    def _process_job(self, job, jobnr):
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
        jobnr = 1
        # Keep running as long as there are jobs in queue
        while self.pool.isactive:
            try:
                # get next queue item, block for _QUEUE_TIMEOUT seconds if empty
                job = self.inqueue.get(True, _QUEUE_TIMEOUT)
            except Queue.Empty:
                print self.name, ": Nothing more to do. Exiting..."
                break
            
            job_result = self._process_job(job, jobnr)    
            
            self.outqueue.put(job_result)
            self.inqueue.task_done()
            jobnr += 1
        self._end_logging()
            

# TODO: check return code of subprocess
class GenericWorker(Worker):
    """Generic worker class derived from Worker baseclass."""
    
    def _process_job(self, job, jobnr):
        cmd = [ job.bin ] + job.args
        try:
            self.process = subprocess.Popen(cmd, shell=False, cwd=job.path,
                                            stdout=self.outfile_handle,
                                            stderr=self.errfile_handle)
            print self.name, "(", jobnr, "): ", job.descr, "..."
            retcode = self.process.wait()
            if retcode < 0:
                print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", job.bin, " terminated with signal", -retcode
            else:
                print self.name, "(", jobnr, "): Ok."
        except OSError, e:
            print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", job.bin, " execution failed:", e
            
        # FIXME: Return something useful
        return job
 
                    
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

