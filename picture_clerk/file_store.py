"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""


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

