"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import urlparse

import config
import index
import repo

from testlib import MockConnector
from app import App


class MockPicture(object):

    def __init__(self, filename):
        self.filename = filename

    def __repr__(self):
        return "Picture(%s)" % self.filename

    def __str__(self):
        return self.filename


class Test(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        pics = (MockPicture('path1'),
                MockPicture('path2'),
                MockPicture('path3'))
        self.index = index.PictureIndex()
        self.index.add_many(pics)
        self.default_conf = config.Config(config.REPO_CONFIG)

    def tearDown(self):
        pass

    def test_init(self):
        app = App(self.connector)
        app.init()

        # load repo from disk and check it's config & index
        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        self.assertTrue(self.connector.opened(config.INDEX_FILE))
        r = repo.Repo.load_from_disk(self.connector)
        self.assertEqual(r.config, self.default_conf)
        self.assertIsNot(r.config, self.default_conf)
        self.assertEqual(r.index, index.PictureIndex())
        self.assertIsNot(r.index, index.PictureIndex())

    @mock.patch('os.path.exists')
    def test_add_pics(self, mock_exists):
        app = App(self.connector)
        repo.Repo.create_on_disk(self.connector,
                                     self.default_conf,
                                     self.index)

        app.add_pics(('path4', 'path5'),
                     process_enabled=False)

        # load repo from disk and check it's config & index
        r = repo.Repo.load_from_disk(self.connector)
        self.assertIn('path4', r.index) # new pics should be in index
        self.assertIn('path5', r.index)
        self.assertIn('path1', r.index) # old pics should still be in index
        self.assertIn('path2', r.index)
        self.assertIn('path3', r.index)
        self.assertEqual(r.config, self.default_conf) # config should not change

    def test_list_pics(self):
        app = App(self.connector)
        repo.Repo.create_on_disk(self.connector,
                                 self.default_conf,
                                 self.index)

        self.assertEqual(app.list_pics(), "path1\npath2\npath3")


if __name__ == "__main__":
    unittest.main()
