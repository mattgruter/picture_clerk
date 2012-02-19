"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock
import os
import StringIO
import contextlib

import connector
import config
import index

from repo import Repo


class BasicTests(unittest.TestCase):

    def setUp(self):
        self.index = mock.Mock()
        self.config = mock.Mock()
        self.connector = mock.Mock()

    def tearDown(self):
        pass

    def test_attributes(self):
        repo = Repo(self.index, self.config, self.connector)
        self.assertIsInstance(repo, Repo)
        self.assertIs(repo.index, self.index)
        self.assertIs(repo.config, self.config)
        self.assertIs(repo.connector, self.connector)

    @unittest.skip
    def test_save_to_disk(self):
        #@todo
        self.assertTrue(False)


class FactoryTests(unittest.TestCase):

    def mock_open(self, path, mode):
        if os.path.basename(path) == 'config':
            return self.conf_buf
        else:
            return self.pi_buf

    def create_mock_connector(self):
        con = mock.Mock(spec_set=connector.Connector)
        con.exists = mock.Mock(return_value=True)
        con.open = self.mock_open
        return con

    def create_mock_file(self, obj):
        buf = StringIO.StringIO()
        obj.write(buf)
        buf.seek(0)
        cm = contextlib.closing(buf)
        return cm

    def setUp(self):
        self.conf = config.Config.from_dict({'index.file': 'index-path'})
        self.pi = index.PictureIndex({'pic1': 'fileA', 'pic2': 'fileB'})

    @unittest.skip
    def test_create_on_disk(self):
        #@todo
        self.assertTrue(False)

    def test_load_from_disk(self):
        self.conf_buf = self.create_mock_file(self.conf)
        self.pi_buf = self.create_mock_file(self.pi)
        con = self.create_mock_connector()
        repo = Repo.load_from_disk(con)
        self.assertEqual(repo.connector, con)
        self.assertEqual(repo.config['index.file'], 'index-path')
        self.assertEqual(repo.index, self.pi)

    @unittest.skip
    def test_clone(self):
        #@todo
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
