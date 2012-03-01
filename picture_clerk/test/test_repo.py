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

from testlib import MockConnector, MockPicture
from index import PictureIndex
from repo import Repo, NotFoundError, VersionMismatchError


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


class LoadTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/baseurl/repo/'))
        self.pi = index.PictureIndex()
        self.pi.add(MockPicture.create_many(10))
        self.conf = config.Config(config.REPO_CONFIG)
        self.conf['index.file'] = 'mock-index-path'
        Repo.create_on_disk(self.connector, self.conf, self.pi)
        self.connector.connect()

    def tearDown(self):
        self.connector.disconnect()

    def test_load_config_from_disk(self):
        repo = Repo(index={}, config={}, connector=self.connector)
        repo.load_config_from_disk()

        self.assertEqual(repo.config, self.conf)
        self.assertIsNot(repo.config, self.conf)
        self.assertEqual(repo.index, {})

    def test_load_index_from_disk(self):
        repo = Repo(index={}, config=self.conf, connector=self.connector)
        repo.load_index_from_disk()

        self.assertEqual(repo.index, self.pi)
        self.assertIsNot(repo.index, self.pi)

    def test_load_index_version_current(self):
        repo = Repo(index={}, config=self.conf, connector=self.connector)
        repo.load_index_from_disk(config.INDEX_FORMAT_VERSION)

        self.assertEqual(repo.index, self.pi)
        self.assertIsNot(repo.index, self.pi)

    def test_load_index_version_1(self):
        repo = Repo(index={}, config=self.conf, connector=self.connector)
        repo.load_index_from_disk(1)

        self.assertEqual(repo.index, self.pi)
        self.assertIsNot(repo.index, self.pi)

    def test_load_index_version_too_low(self):
        repo = Repo(index={}, config=self.conf, connector=self.connector)

        self.assertRaises(KeyError, repo.load_index_from_disk, 0)

    def test_load_version_mismatch_error(self):
        repo = Repo(index={}, config=self.conf, connector=self.connector)

        with self.assertRaises(VersionMismatchError) as cm:
            repo.load_index_from_disk(99)
        self.assertEqual(cm.exception.actual, 99)
        self.assertEqual(cm.exception.expected, config.INDEX_FORMAT_VERSION)


class SaveTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/baseurl/repo/'))
        self.pi = index.PictureIndex()
        self.pi.add(MockPicture.create_many(10))
        self.conf = config.Config(config.REPO_CONFIG)
        self.conf['index.file'] = 'mock-index-path'
        self.connector.connect()

    def tearDown(self):
        self.connector.disconnect()

    def test_save_config_to_disk(self):
        repo = Repo(self.pi, self.conf, self.connector)
        repo.save_config_to_disk()

        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        config_on_disk = config.Config()
        config_on_disk.read(self.connector.get_file(config.CONFIG_FILE))
        self.assertEqual(config_on_disk, self.conf)
        self.assertIsNot(config_on_disk, self.conf)

    def test_save_index_to_disk(self):
        repo = Repo(self.pi, self.conf, self.connector)
        repo.save_index_to_disk()

        self.assertTrue(self.connector.opened('mock-index-path'))
        index_on_disk = index.PictureIndex()
        index_on_disk.read(self.connector.get_file('mock-index-path'))
        self.assertEqual(index_on_disk, self.pi)
        self.assertIsNot(index_on_disk, self.pi)


class FactoryTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/baseurl/repo/'))
        self.pi = index.PictureIndex()
        self.pi.add(MockPicture.create_many(10))
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

    def test_load_from_disk(self):
        repo_created = Repo.create_on_disk(self.connector, self.conf, self.pi)
        repo_loaded = Repo.load_from_disk(self.connector)

        self.assertIsInstance(repo_loaded, Repo)
        self.assertEqual(repo_loaded.config, repo_created.config)
        self.assertIsNot(repo_loaded.config, repo_created.config)
        self.assertEqual(repo_loaded.index, repo_created.index)
        self.assertIsNot(repo_loaded.index, repo_created.index)
        self.assertIsNot(repo_loaded, repo_created)
        self.assertIs(repo_loaded.connector, self.connector)

    def test_load_notfound_error(self):
        self.connector.exists = mock.Mock(return_value=False)
        with self.assertRaises(NotFoundError) as cm:
            Repo.load_from_disk(self.connector)
        self.assertEqual(cm.exception.url, self.connector.url)

    def test_load_version_mismatch_error(self):
        self.conf['index.format_version'] = 99
        Repo.create_on_disk(self.connector, self.conf, self.pi)

        with self.assertRaises(VersionMismatchError) as cm:
            Repo.load_from_disk(self.connector)
        self.assertEqual(cm.exception.actual, 99)
        self.assertEqual(cm.exception.expected, config.INDEX_FORMAT_VERSION)

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
