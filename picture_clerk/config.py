"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os.path
import ConfigParser
import collections


## application level defaults
APP_SHORT_NAME = "pic"

# application global config/log directory
APP_DIR = os.path.join(os.path.expanduser('~'), '.' + APP_SHORT_NAME)

# application global logging
APP_LOG_FILE = os.path.join(APP_DIR, 'log')

# application global config file
APP_CONFIG_FILE = os.path.join(APP_DIR, 'config')

# number of workers in each stage by default
STAGE_SIZE = 1

# number of seconds a worker should wait for new jobs if queue is empty
WORKER_TIMEOUT = 1

# path to exiv2 executable (used by Exiv2XMPSidecarWorker)
EXIV2_BIN = '/usr/bin/exiv2'

# path to jhead executable (used by AutorotWorker)
JHEAD_BIN = '/usr/bin/jhead'

# default viewer program
VIEWER = 'qiv -m -t'


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
        except ConfigParser.NoSectionError:  # create section if it doesn't exist
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

    def todict(self):
        """Return the configuration as a dictionary."""
        return dict(self.iteritems())

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


def new_app_config():
    """Return default app configuration (Config instance)."""

    APP_CONFIG = {
        'logging.file': APP_LOG_FILE,
        'pipeline.stagesize': STAGE_SIZE,
        'pipeline.workertimeout': WORKER_TIMEOUT,
        'tools.exiv2': EXIV2_BIN,
        'tools.jhead': JHEAD_BIN,
        'viewer.prog': VIEWER,
                }

    return Config(APP_CONFIG)
