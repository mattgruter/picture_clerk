"""
Created on 2012/02/19

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import StringIO
import collections

from connector import Connector


class MockFile(StringIO.StringIO):

    def __init__(self):
        StringIO.StringIO.__init__(self)

    def close(self):
        self.seek(0)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        self.close()


class MockConnector(Connector):

    def __init__(self, url):
        Connector.__init__(self, url)
        self.buffers = collections.defaultdict(MockFile)

    def _connect(self):
        pass

    def _disconnect(self):
        pass

    def _exists(self, path):
        return True

    def _mkdir(self, path, mode):
        pass

    def _open(self, path, mode):
        return self.buffers[path]

    def _remove(self, path):
        pass

    def opened(self, rel_path):
        return self._rel2abs(rel_path) in self.buffers

    def get_file(self, rel_path):
        return self.buffers[self._rel2abs(rel_path)]



