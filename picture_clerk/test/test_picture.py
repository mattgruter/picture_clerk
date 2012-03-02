"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL
"""
import unittest

import copy
import hashlib
import os

from picture import get_sha1


class ChecksumTests(unittest.TestCase):

    def setUp(self):
        self.buf = os.urandom(1024 ** 2) # 1MB random bytes

    def tearDown(self):
        pass

    def test_sha1(self):
        self.assertEqual(get_sha1(self.buf),
                         hashlib.sha1(self.buf).hexdigest())

    def test_determinism(self):
        buf2 = copy.copy(self.buf)
        self.assertEqual(get_sha1(self.buf),
                         get_sha1(buf2))


if __name__ == "__main__":
    unittest.main()
