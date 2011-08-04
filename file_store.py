"""file_store.py

File system access tools
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/21 $"
__copyright__ = "Copyright (c) 2011 Matthias Grueter"
__license__ = "GPL"


# Exceptions
class FileAlreadyOpenError(Exception):
    pass
    
class FileNotOpenError(Exception):
    pass


# Base class
class FileStore(object):
    def __init__(self, path):
        self.path = path
        self._fh = None
        self.opened = False

    def open(self, revision):
        raise NotImplementedError
        
    def close(self):
        raise NotImplementedError
        
    def commit(self):
        raise NotImplementedError
        
    def rollback(self):
        raise NotImplementedError
        
    def get_log(self, limit):
        raise NotImplementedError
        
