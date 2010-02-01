"""config.py

PictureClerk - The little helper for your picture workflow.
This file contains global configurations
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


# number of workers in each stage by default
DEFAULT_NUM_STAGEWORKERS = 1

# number of seconds a worker should wait for new jobs if queue is empty
WORKER_TIMEOUT = 1

# full path to DCRaw executable
DCRAW_BIN = '/usr/bin/dcraw'
# full path to git executable
GIT_BIN = '/usr/bin/git'
# full path to exiv2 executable
EXIV2_BIN = '/usr/bin/exiv2'
# full path to jhead executable
JHEAD_BIN = '/usr/bin/jhead'

# cache file name
CACHE_FILE = '.pic.db'

# file pattern for import
IMPORT_FILE_PATTERN = '*.NEF'

# loggin on/off
LOGGING=True
# logging dir
LOGDIR='log/'
