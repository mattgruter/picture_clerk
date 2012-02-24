"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import urlparse
import hashlib

import config
import index
import repo
import picture

from testlib import MockConnector
from app import App


class TestApp(unittest.TestCase):

    def setUp(self):
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.pics = [picture.Picture('DSC_%04i.NEF' % i)
                     for i in range(32, 10, -1)]
        for pic in self.pics:
            pic.checksum = hashlib.sha1(pic.filename).hexdigest()
            pic.add_sidecar(pic.basename + '.thumb.jpg', 'thumbnail')
        self.index = index.PictureIndex()
        self.index.add(self.pics)
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
        repo.Repo.create_on_disk(self.connector,
                                     self.default_conf,
                                     self.index)
        app = App(self.connector)
        app.add_pics(('testfile1', 'testfile2'), process_enabled=False)

        # load repo from disk and check it's config & index
        r = repo.Repo.load_from_disk(self.connector)
        self.assertIn('testfile1', r.index) # new pics should be in index
        self.assertIn('testfile2', r.index)
        for old_pic in self.pics: # old pics should still be in index
            self.assertIn(old_pic.filename, r.index)
        self.assertEqual(r.config, self.default_conf) # config should not change

    def test_remove_pics(self):
        repo.Repo.create_on_disk(self.connector,
                                     self.default_conf,
                                     self.index)
        app = App(self.connector)
        pics_to_remove = self.pics[2:5]
        pics_remaining = self.pics[:2] + self.pics[5:]
        app.remove_pics((pic.filename for pic in pics_to_remove))

        # load repo from disk and check it's config & index
        r = repo.Repo.load_from_disk(self.connector)
        for pic in pics_to_remove:
            self.assertNotIn(pic.filename, r.index)
        for pic in pics_remaining:
            self.assertIn(pic.filename, r.index)
        self.assertEqual(r.config, self.default_conf) # config should not change

        # check that correct files were removed
        for pic in pics_to_remove:
            for picfile in pic.get_filenames():
                self.assertTrue(self.connector.removed(picfile))
        for pic in pics_remaining:
            for picfile in pic.get_filenames():
                self.assertFalse(self.connector.removed(picfile))

    def test_list_pics(self):
        repo.Repo.create_on_disk(self.connector,
                                 self.default_conf,
                                 self.index)
        app = App(self.connector)

        # list all
        list_all_template = "%s\n  Sidecar files:\n   thumbnail: %s"
        list_all_expected = '\n'.join([(list_all_template %
                                        (pic.filename,
                                         pic.get_thumbnail_filenames()[0]))
                                       for pic in sorted(self.pics)])
        self.assertEqual(app.list_pics("all"), list_all_expected)

        # list thumbnails
        self.assertSequenceEqual(app.list_pics("thumbnails").split('\n'),
                                 ['\n'.join(pic.get_thumbnail_filenames())
                                  for pic in sorted(self.pics)])

        # list sidecars
        self.assertSequenceEqual(app.list_pics("sidecars").split('\n'),
                                 ['\n'.join(pic.get_sidecar_filenames())
                                  for pic in sorted(self.pics)])

        # list checksums
        self.assertSequenceEqual(app.list_pics("checksums").split('\n'),
                                 ['%s *%s' % (pic.checksum, pic.filename)
                                  for pic in sorted(self.pics)])

@mock.patch('app.App.remove_pics')
@mock.patch('app.Viewer', spec_set=True)
class TestViewer(unittest.TestCase):

    def setUp(self):
        # test pictures
        self.pics = [picture.Picture('DSC_%04i.NEF' % i)
                     for i in range(32, 10, -1)]
        for pic in self.pics:
            pic.checksum = hashlib.sha1(pic.filename).hexdigest()
            pic.add_sidecar(pic.basename + '.thumb.jpg', 'thumbnail')
        pi = index.PictureIndex()
        pi.add(self.pics)
        self.thumbs = [pic.get_thumbnail_filenames()[0] for pic in self.pics]

        # test repo
        self.connector = MockConnector(urlparse.urlparse('/basedir/repo/'))
        self.default_conf = config.Config(config.REPO_CONFIG)
        repo.Repo.create_on_disk(self.connector, self.default_conf, pi)

    def tearDown(self):
        pass

    def test_default_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        app = App(self.connector)
        app.view_pics(prog=None)

        MockViewer.assert_called_once_with(self.default_conf['viewer.prog'])
        mock_viewer_inst.show.assert_called_once_with(sorted(self.thumbs))
        mock_remove_pics.assert_called_once_with([])

    def test_supplied_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        app = App(self.connector)
        prog = 'awesome-viewer-app arg1 --opt1 -o2'
        app.view_pics(prog)

        MockViewer.assert_called_once_with(prog)
        mock_viewer_inst.show.assert_called_once_with(sorted(self.thumbs))
        mock_remove_pics.assert_called_once_with([])

    def test_removing_pics(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = self.thumbs[4:7]

        app = App(self.connector)
        app.view_pics(prog=None)

        mock_remove_pics.assert_called_with(self.thumbs[4:7])



if __name__ == "__main__":
    unittest.main()
