"""file_store.py

File system access tools
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/23 $"
__copyright__ = "Copyright (c) 2011 Matthias Grueter"
__license__ = "GPL"


from file_store import FileStore
from file_store import FileAlreadyOpenError, FileNotOpenError


        
class PlainFileStore(FileStore):
    def __init__(self, path):
        FileStore.__init__(self, path)
        
    def open(self, mode):
        if not self._fh:
            self._fh = open(self.path, mode)
            self.opened = True
        else:
            raise FileAlreadyOpenError
        
    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None
            self.opened = False
        else:
            raise FileNotOpenError
        
    def get_log(self, limit):
        return []
        
