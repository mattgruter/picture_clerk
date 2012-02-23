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
import logging
import ConfigParser
import collections

# application name
APP_NAME = "PictureClerk"
APP_SHORT_NAME = "pic"
APP_EXEC_NAME = "pic"

# application global config/log directory
APP_DIR = os.path.join(os.path.expanduser('~'), '.' + APP_SHORT_NAME)

# application global logging
APP_LOG_FILE = os.path.join(APP_DIR, 'log')

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

# worker logging on/off
LOGGING = True
LOGDIR = os.path.join(PIC_DIR, "log")

# repo logging
REPO_LOG_FILE = os.path.join(PIC_DIR, "log.txt")
REPO_LOG_LEVEL = logging.DEBUG
REPO_LOG_FORMAT = '%%(asctime)s %%(name)-15s %%(levelname)-8s %%(message)s'

# SHA1 sidecar files on/off
SHA1_SIDECAR_ENABLED = 1
SHA1_SIDECAR_DIR = os.path.join(PIC_DIR, "sha1")

# ThumbWorker configuration
THUMB_SIDECAR_DIR = "jpg"
THUMB_COPY_METADATA = 1

# XMP metadata sidecar file destination
XMP_SIDECAR_DIR = os.path.join(PIC_DIR, "xmp")

# default processing instructions/recipe used if none defined at command line
DEFAULT_RECIPE = "HashDigestWorker, ThumbWorker, AutorotWorker, MetadataWorker"

# viewer
VIEWER_CMD = "qiv -m -t"

REPO_CONFIG = {
    'index.file': INDEX_FILE,
    'index.format_version': INDEX_FORMAT_VERSION,
    'recipes.default': DEFAULT_RECIPE,
    'thumbnails.sidecar_dir': THUMB_SIDECAR_DIR,
    'thumbnails.copy_metadata': THUMB_COPY_METADATA,
    'checksums.sidecar_enabled': SHA1_SIDECAR_ENABLED,
    'checksums.sidecar_dir': SHA1_SIDECAR_DIR,
    'logging.file': REPO_LOG_FILE,
    'logging.level': REPO_LOG_LEVEL,
    'logging.format': REPO_LOG_FORMAT,
    'viewer.prog': VIEWER_CMD,
               }

class Config(collections.MutableMapping):
    """
    Configuration
    """

    def __init__(self, d=None):
        """
        Constructor
        """
        self._parser = ConfigParser.SafeConfigParser()
        if d:
            for key, value in d.iteritems():
                self[key] = value


    def __getitem__(self, key):
        try:
            section, option = key.split('.')
        except ValueError:
            raise KeyError(key)
        try:
            value = self._parser.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise KeyError(key)
        return self.parse_string_value(value)

    def __setitem__(self, key, value):
        try:
            section, option = key.split('.')
        except ValueError:
            #@todo: raise more descriptive exception
            raise KeyError(key)
        try:
            self._parser.set(section, option, str(value))
        except ConfigParser.NoSectionError: # create section if it doesn't exist
            self._parser.add_section(section)
            self[key] = value

    def __delitem__(self, key):
        section, option = key.split('.')
        self._parser.remove_option(section, option)

    def __len__(self):
        return len(list(self.__iter__()))

    def __iter__(self):
        for section in self._parser.sections():
            for option in self._parser.options(section):
                yield section + '.' + option

    def __contains__(self, key):
        section, option = key.split('.')
        return self._parser.has_option(section, option)

    def __str__(self):
        res = ('%s: %s' % (repr(k), repr(v)) for k, v in self.iteritems())
        return '{%s}' % ', '.join(res)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def parse_string_value(self, value):
        """Parse the supplied string and cast it to int or float if applicable.
        
        The value is first cast to int, if that fails it is cast to float and
        if that also fails the value is returned unchanged.
        
        Arguments:
        value -- string representation of either an int, float or string.
        
        """
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            return value

    def write(self, fh):
        """Write configuration file (same file format as ConfigParser).
        
        Arguments:
        fh -- writable file-like object
        
        """
        self._parser.write(fh)

    def read(self, fh):
        """Read configuration from a ConfigParser file.
        
        Arguments:
        fh -- readable file-like object
        
        """
        self._parser.readfp(fh)

    @classmethod
    def from_dict(cls, d):
        """Populate new Config instance with data from dict and return it."""
        return Config(d)

    @classmethod
    def from_configparser(cls, cp):
        """Return new Config instance with data from supplied ConfigParser."""
        conf = Config()
        for section in cp.sections():
            for option in cp.options(section):
                key = section + '.' + option
                value = cp.get(section, option)
                conf[key] = value
        return conf

