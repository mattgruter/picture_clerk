"""pic_import.py

PictureClerk - The little helper for your picture workflow.
Imports negatives into a repository using Jobs, Workers and Pipelines
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/06/15 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"

import os
import sys
import fnmatch

from worker import Worker
from job import Job
from pipeline import Pipeline


# globals
GIT = "/usr/bin/git"
DCRAW = "/usr/bin/dcraw"
EXIV2 = "/usr/bin/exiv2"



def create_repo(path):
    """Initialize repository and add pictures to it."""

    dirlist = os.listdir(path)
    files = fnmatch.filter(dirlist, "*.NEF")

#    git_job1 = Job(GIT, [ 'init' ], 'Initializing Git repository')
#    git_job2 = Job(GIT, [ 'add' ] + files, 'Adding pictures to repository')
#    git_job3 = Job(GIT, [ 'commit', '-m', 'Importing negatives' ], 'Commiting to repository...')
#    git_queue.put(git_job1)
#    git_queue.put(git_job2)
#    git_queue.put(git_job3)

#    dcraw_job1 = Job(DCRAW, [ '-e' ] + files, 'Generating thumbnails')
#    dcraw_queue.put(dcraw_job1)

#    exiv2_job1 = Job(EXIV2, [ '-e', 'X', 'ex' ] + files, 'Extracting metadata')
#    exiv2_queue.put(exiv2_job1)
#    
#    worker_git = Worker('git', path, git_queue, 'Git Pipeline')
#    worker_git.start()
#    worker_dcraw = Worker('dcraw', path, dcraw_queue, 'DCRaw Pipeline')
#    worker_dcraw.start()
#    worker_exiv2 = Worker('exiv2', path, exiv2_queue, 'Exiv2 Pipeline')
#    worker_exiv2.start()

#    git_queue.join()
#    dcraw_queue.join()
#    exiv2_queue.join()


if __name__ == "__main__":
    import sys
    import getopt
    try:
        create_repo("test")
    except KeyboardInterrupt:
        print "Exiting."
        sys.exit(None)

