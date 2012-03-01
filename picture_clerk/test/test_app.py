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

from testlib import MockConnector, MockPicture
from app import App


def create_mock_repo(connector):
    # test index
    pi = index.PictureIndex()
    pi.add(MockPicture.create_many(20))

    # test config
    conf = config.Config(config.REPO_CONFIG)
    conf['index.file'] = ".pic/testindex"
    conf['test.test'] = "foo"

    return repo.Repo.create_on_disk(connector, conf, pi)


class InitRepoTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))

    def tearDown(self):
        pass

    def test_init_repo(self):
        app = App(self.connector)
        app.init_repo()

        # check that config & files were opened
        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        self.assertTrue(self.connector.opened(config.INDEX_FILE))
        # load initializied repo from disk and check index & config
        r = repo.Repo.load_from_disk(self.connector)
        # repo config should be default config
        self.assertEqual(r.config, config.Config(config.REPO_CONFIG))
        # repo index should be empty
        self.assertEqual(r.index, index.PictureIndex())


class LoadRepoTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.repo = create_mock_repo(self.connector)

    def tearDown(self):
        pass

    def test_load_repo(self):
        app = App(self.connector)
        app.load_repo()

        self.assertEqual(app.repo.index, self.repo.index)
        self.assertEqual(app.repo.config, self.repo.config)
        self.assertIsNot(app.repo, self.repo)
        # check that correct config & index files were opened
        self.assertTrue(self.connector.opened(config.CONFIG_FILE))
        self.assertTrue(self.connector.opened(self.repo.config['index.file']))


class AddRemovePicsTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.repo = create_mock_repo(self.connector)

    def tearDown(self):
        pass

    @mock.patch('os.path.exists')
    def test_add_pics(self, mock_exists):
        app = App(self.connector, self.repo)
        app.add_pics(('testfile1', 'testfile2'), process_enabled=False)

        # load repo from disk and check it's config & index
        r = repo.Repo.load_from_disk(self.connector)
        self.assertEqual(r.index, self.repo.index)
        self.assertIn('testfile1', r.index) # new pics should be in index
        self.assertIn('testfile2', r.index)
        for old_pic in self.repo.index.iterpics(): # old pics should still be in index
            self.assertIn(old_pic.filename, r.index)

    def test_remove_pics(self):
        app = App(self.connector, self.repo)
        pics = self.repo.index.pics()
        pics_to_remove = pics[2:5]
        pics_remaining = pics[:2] + pics[5:]
        app.remove_pics((pic.filename for pic in pics_to_remove))

        # load repo from disk and check it's config & index
        r = repo.Repo.load_from_disk(self.connector)
        self.assertEqual(r.index, self.repo.index)
        for pic in pics_to_remove:
            self.assertNotIn(pic.filename, r.index)
        for pic in pics_remaining:
            self.assertIn(pic.filename, r.index)

        # check that correct files were removed
        for pic in pics_to_remove:
            for picfile in pic.get_filenames():
                self.assertTrue(self.connector.removed(picfile))
        for pic in pics_remaining:
            for picfile in pic.get_filenames():
                self.assertFalse(self.connector.removed(picfile))


class ListPicsTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.repo = create_mock_repo(self.connector)

    def tearDown(self):
        pass

    def test_list_all(self):
        app = App(self.connector, self.repo)
        template = "%s\n  Sidecar files:\n   thumbnail: %s"
        expected = '\n'.join([template % (pic.filename,
                                          pic.get_thumbnail_filenames()[0])
                              for pic in self.repo.index.pics()])
        self.assertEqual(app.list_pics("all"), expected)

    def test_list_thumbnails(self):
        app = App(self.connector, self.repo)
        expected = '\n'.join(['\n'.join(pic.get_thumbnail_filenames())
                              for pic in self.repo.index.pics()])
        self.assertSequenceEqual(app.list_pics('thumbnails'), expected)

    def test_list_sidecars(self):
        app = App(self.connector, self.repo)
        expected = '\n'.join(['\n'.join(pic.get_sidecar_filenames())
                              for pic in self.repo.index.pics()])
        self.assertSequenceEqual(app.list_pics('sidecars'), expected)

    def test_list_checksums(self):
        app = App(self.connector, self.repo)
        expected = '\n'.join(['%s *%s' % (pic.checksum, pic.filename)
                              for pic in self.repo.index.pics()])
        self.assertSequenceEqual(app.list_pics('checksums'), expected)


@mock.patch('app.App.remove_pics')
@mock.patch('app.Viewer', spec_set=True)
class ViewPicsTests(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.repo = create_mock_repo(self.connector)

    def tearDown(self):
        pass

    def test_default_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        app = App(self.connector, self.repo)
        app.view_pics(prog=None)

        MockViewer.assert_called_once_with(self.repo.config['viewer.prog'])
        mock_viewer_inst.show.assert_called_once_with(self.repo.index.pics())
        mock_remove_pics.assert_called_once_with([])

    def test_supplied_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        app = App(self.connector, self.repo)
        prog = 'awesome-viewer-app arg1 --opt1 -o2'
        app.view_pics(prog)

        MockViewer.assert_called_once_with(prog)
        mock_viewer_inst.show.assert_called_once_with(self.repo.index.pics())
        mock_remove_pics.assert_called_once_with([])

    def test_removing_pics(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = self.repo.index.pics()[4:7]

        app = App(self.connector, self.repo)
        app.view_pics(prog=None)

        pic_filenames = [pic.filename for pic in self.repo.index.pics()[4:7]]
        mock_remove_pics.assert_called_with(pic_filenames)



if __name__ == "__main__":
    unittest.main()
