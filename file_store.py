"""file_store.py

File system access tools
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/01 $"
__copyright__ = "Copyright (c) 2011 Matthias Grueter"
__license__ = "GPL"


# Git support
from dulwich.objects import Blob, Tree, Commit
import time


class FileStore(object):
    def open(self, path, revision):
        return None
        
    def commit(self, path):
        pass
        
    def rollback(self, path):
        pass
        
    def get_log(self, path, limit):
        return []
        
        
class PlainFileStore(FileStore):
    def open(self, path):
        return open(path)
        
