"""pic_create_repo.py

PictureClerk - The little helper for your picture workflow.
This file contains the function that handles repository creation
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/06/15 $"
__copyright__ = "Copyright (c) 2007 Matthias Grueter"
__license__ = "GPL"

import subprocess
import os
import sys
import fnmatch
import threading
import Queue


# globals
GIT = "/usr/bin/git"
DCRAW = "/usr/bin/dcraw"
EXIV2 = "/usr/bin/exiv2"
git_queue = Queue.Queue()
dcraw_queue = Queue.Queue()
exiv2_queue = Queue.Queue()
#num_git_threads = 5
#num_dcraw_threads = 5


#try:
#    import pyexiv2
#except ImportError:
#    print 'You need to install the pyexiv2 package.'
#    sys.exit(1)


class Job():
    def __init__(self, bin, args, descr):
        """Class to organize job orders for workers

        Constructor arguments:
        bin (string)    :   binary to execute
        args (list)     :   arguments to be passed to binary
        descr (string)  :   descriptive text for use in logging and such."""

        self.bin = bin
        self.args = args
        self.descr = descr


# TODO:
# - error/execption handling in thread class or outside?
# - check return code of subprocess
class Worker(threading.Thread):
    """Worker is a thread class who works on jobs coming from a queue.

    Constructor arguments:
        name (string)       :   unique identifier of worker
        path (string)       :   filesystem path in which the worker should conduct his work
        queue (Queue.Queue) :   queue from which worker gets his jobs.
        descr (string)      :   descriptive text for logging and such"""

    def __init__(self, name, path, queue, descr):
        threading.Thread.__init__(self)
        self.name = name        
        self.path = path
        self.queue = queue
        self.descr = descr
        self.outfile = self.path + '/' + self.name + '.log'
        self.outfile_handle=open(self.outfile, 'w')
        self.errfile = self.path + '/' + self.name + '.err'
        self.errfile_handle=open(self.errfile, 'w')

    def run(self):
        jobnr = 1
        # Keep running as long as there are jobs in queue
        while True:
            try:
                # get next queue item, block for 3 seconds if empty
                job = self.queue.get(True, 3)
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


def create_repo(path):
    """Initialize repository and add pictures to it."""

    dirlist = os.listdir(path)
    files = fnmatch.filter(dirlist, "*.NEF")

    git_job1 = Job(GIT, [ 'init' ], 'Initializing Git repository')
    git_job2 = Job(GIT, [ 'add' ] + files, 'Adding pictures to repository')
    git_job3 = Job(GIT, [ 'commit', '-m', 'Importing negatives' ], 'Commiting to repository...')
    git_queue.put(git_job1)
    git_queue.put(git_job2)
    git_queue.put(git_job3)

    dcraw_job1 = Job(DCRAW, [ '-e' ] + files, 'Generating thumbnails')
    dcraw_queue.put(dcraw_job1)

    exiv2_job1 = Job(EXIV2, [ '-e', 'X', 'ex' ] + files, 'Extracting metadata')
    exiv2_queue.put(exiv2_job1)
    
    worker_git = Worker('git', path, git_queue, 'Git Pipeline')
    worker_git.start()
    worker_dcraw = Worker('dcraw', path, dcraw_queue, 'DCRaw Pipeline')
    worker_dcraw.start()
    worker_exiv2 = Worker('exiv2', path, exiv2_queue, 'Exiv2 Pipeline')
    worker_exiv2.start()

    git_queue.join()
    dcraw_queue.join()
    exiv2_queue.join()


if __name__ == "__main__":
    import sys
    import getopt
    try:
        create_repo("test")
    except KeyboardInterrupt:
        print "Exiting."
        sys.exit(None)

