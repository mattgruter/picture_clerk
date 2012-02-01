"""config.py

PictureClerk - The little helper for your picture workflow.
This file contains global configurations
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


import os.path


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

# file pattern for import
IMPORT_FILE_PATTERN = '*.NEF'

# PictureClerk directory
PIC_DIR = ".pic"

# config file
CONFIG_FILE = os.path.join(PIC_DIR, "config")

# default picture index file
INDEX_FILE = os.path.join(PIC_DIR, "index")

# index format version
INDEX_FORMAT_VERSION = 1

# logging on/off
LOGGING = True
LOGDIR = os.path.join(PIC_DIR, "log")

# SHA1 sidecar files on/off
SHA1_SIDECAR_ENABLED = True
SHA1_SIDECAR_DIR = os.path.join(PIC_DIR, "sha1")

# ThumbWorker configuration
THUMB_SIDECAR_DIR = "jpg"
THUMB_COPY_METADATA = True

# XMP metadata sidecar file destination
XMP_SIDECAR_DIR = os.path.join(PIC_DIR, "xmp")

# default processing instructions/recipe used if none defined at command line
DEFAULT_RECIPE = "HashDigestWorker, ThumbWorker, AutorotWorker, MetadataWorker"
