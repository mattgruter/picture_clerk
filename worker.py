"""worker.py

PictureClerk - The little helper for your picture workflow.
This file contains the Worker class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2007 Matthias Grueter"
__license__ = "GPL"

import sys
import threading
import Queue
import subprocess


# Time in seconds to wait before Worker exits when its queue is empty
_QUEUE_TIMEOUT = 3


# TODO: error/execption handling in thread class or outside?
# TODO: check return code of subprocess
# TODO: unit tests
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

    def __init__(self, name, seq_num=1, path, queue, descr):
        threading.Thread.__init__(self)
        self.name = name        
        self.path = path
        self.queue = queue
        self.descr = descr
        self.seq_num = seq_num

    def run(self):
        # Logging
        self.outfile = self.path + '/' + self.name + '.log'
        self.outfile_handle=open(self.outfile, 'w')
        self.errfile = self.path + '/' + self.name + '.err'
        self.errfile_handle=open(self.errfile, 'w')
        
        jobnr = 1
        # Keep running as long as there are jobs in queue
        while True:
            try:
                # get next queue item, block for _QUEUE_TIMEOUT seconds if empty
                job = self.queue.get(True, _QUEUE_TIMEOUT)
            except Queue.Empty:
                print self.name, ": Nothing more to do. Exiting..."
                break
            cmd = [ job.bin ] + job.args
            try:
                self.process = subprocess.Popen(cmd, shell=False, cwd=self.path, stdout=self.outfile_handle, stderr=self.errfile_handle)
                print self.name, "(", jobnr, "): ", job.descr, "..."
                retcode = self.process.wait()
                if retcode < 0:
                    print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", job.bin, " terminated with signal", -retcode
                else:
                    print self.name, "(", jobnr, "): Ok."
            except OSError, e:
                print >>sys.stderr, self.name, "(", jobnr, "): ERROR - ", job.bin, " execution failed:", e
            self.queue.task_done()
            jobnr += 1
            
            
#    class WorkerType():
#        
#        def __init__(self, type_name)
            
            
# Unit test       
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


