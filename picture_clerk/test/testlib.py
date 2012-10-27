"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""

import collections
import hashlib
import random
import StringIO
import sys
import contextlib
import urlparse

from connector import Connector
from picture import Picture


class MockFile(StringIO.StringIO):

    def __init__(self):
        StringIO.StringIO.__init__(self)

    def close(self):
        self.seek(0)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        self.close()

    def __repr__(self):
        return self.buf


class MockConnector(Connector):

    connectors = dict()

    def __init__(self, url):
        Connector.__init__(self, url)
        self.buffers = collections.defaultdict(MockFile)
        self.removed_files = []

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
        self.removed_files.append(path)

    def opened(self, rel_path):
        return self._rel2abs(rel_path) in self.buffers

    def removed(self, rel_path):
        return self._rel2abs(rel_path) in self.removed_files

    def get_file(self, rel_path):
        return self.buffers[self._rel2abs(rel_path)]

    @classmethod
    def from_string(cls, path):
        try:
            return cls.connectors[path]
        except KeyError:
            c = cls(urlparse.urlparse(path))
            cls.connectors[path] = c
            return c


class MockPicture(Picture):

    def __init__(self, filename):
        Picture.__init__(self, filename)
        self.add_sidecar(self.basename + '.thumb.jpg', 'thumbnail')
        self.checksum = hashlib.sha1(filename).hexdigest()

    @classmethod
    def create_many(cls, count, template='DSC_%04i.NEF'):
        pics = [MockPicture(template % i) for i in range(count)]
        random.shuffle(pics)    # randomize list order
        return pics


# from http://stackoverflow.com/questions/1809958/hide-stderr-output-in-unit-tests
@contextlib.contextmanager
def suppress_stderr():
    stderr_orig = sys.stderr
    class DevNull(object):
        def write(self, param):
            pass
    sys.stderr = DevNull()
    yield
    sys.stderr = stderr_orig
