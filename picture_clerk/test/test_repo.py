"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import unittest
import mock
import urlparse

import config
import index

from testlib import MockConnector
from index import PictureIndex
from repo import Repo
from picture import Picture


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

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/baseurl/repo/'))
        self.pi = index.PictureIndex()
        self.pi.add((Picture('pic1'), Picture('pic2'), Picture('pic3')))
        self.conf = config.Config(config.REPO_CONFIG)
        self.conf['index.file'] = 'mock-index-path'

    def test_create_on_disk_empty(self):
        repo = Repo.create_on_disk(self.connector, self.conf)

        # test repo
        self.assertIsInstance(repo, Repo)
        self.assertIs(repo.connector, self.connector)
        self.assertIs(repo.config, self.conf)
        self.assertEqual(repo.index, PictureIndex())

        # test conf on disk
        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        conf_on_disk = config.Config()
        conf_on_disk.read(self.connector.get_file(config.CONFIG_FILE))
        self.assertEqual(conf_on_disk, self.conf)

        # test picture index on disk
        self.assertTrue(self.connector.opened('mock-index-path'))
        index_on_disk = index.PictureIndex()
        index_on_disk.read(self.connector.get_file('mock-index-path'))
        self.assertEqual(index_on_disk, index.PictureIndex())

    def test_create_on_disk_with_index(self):
        repo = Repo.create_on_disk(self.connector, self.conf, self.pi)

        # test repo
        self.assertIsInstance(repo, Repo)
        self.assertIs(repo.connector, self.connector)
        self.assertIs(repo.config, self.conf)
        self.assertEqual(repo.index, self.pi)

        # test conf on disk
        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        conf_on_disk = config.Config()
        conf_on_disk.read(self.connector.get_file(config.CONFIG_FILE))
        self.assertEqual(conf_on_disk, self.conf)

        # test picture index on disk
        self.assertTrue(self.connector.opened('mock-index-path'))
        index_on_disk = index.PictureIndex()
        index_on_disk.read(self.connector.get_file('mock-index-path'))
        self.assertEqual(index_on_disk, self.pi)

    def test_created_and_load_from_disk(self):
        repo_created = Repo.create_on_disk(self.connector, self.conf, self.pi)
        repo_loaded = Repo.load_from_disk(self.connector)

        self.assertIsInstance(repo_loaded, Repo)
        self.assertEqual(repo_loaded.config, repo_created.config)
        self.assertIsNot(repo_loaded.config, repo_created.config)
        self.assertEqual(repo_loaded.index, repo_created.index)
        self.assertIsNot(repo_loaded.index, repo_created.index)
        self.assertIsNot(repo_loaded, repo_created)
        self.assertIs(repo_loaded.connector, self.connector)

    def test_clone(self):
        src_repo = Repo.create_on_disk(self.connector, self.conf, self.pi)
        dest_connector = MockConnector(urlparse.urlparse('/destrepo/baseurl/'))
        dest_repo = Repo.clone(src=self.connector, dest=dest_connector)

        self.assertIsInstance(dest_repo, Repo)
        self.assertEqual(dest_repo.config, src_repo.config)
        self.assertIsNot(dest_repo.config, src_repo.config)
        self.assertEqual(dest_repo.index, src_repo.index)
        self.assertIsNot(dest_repo.index, src_repo.index)
        self.assertIsNot(dest_repo, src_repo)
        self.assertTrue(dest_connector.opened(config.CONFIG_FILE))
        self.assertTrue(dest_connector.opened('mock-index-path'))


if __name__ == "__main__":
    unittest.main()
