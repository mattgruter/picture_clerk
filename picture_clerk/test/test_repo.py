"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock

from repo import Repo


class BasicTests(unittest.TestCase):

    def setUp(self):
        self.index = mock.Mock()
        self.config = mock.Mock()
        self.connector = mock.Mock()

    def tearDown(self):
        pass

    def test_attributes(self):
        """Constructor should return a new Repo with supplied contents."""
        repo = Repo(self.index, self.config, self.connector)
        self.assertIsInstance(repo, Repo)
        self.assertIs(repo.index, self.index)
        self.assertIs(repo.config, self.config)
        self.assertIs(repo.connector, self.connector)


if __name__ == "__main__":
    unittest.main()
