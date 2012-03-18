"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
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

