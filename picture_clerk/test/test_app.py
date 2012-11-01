"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import os

import index
import repo
import app

from testlib import MockConnector, MockPicture, new_mock_repo


@mock.patch('app.Connector', new=MockConnector)
class InitRepoTests(unittest.TestCase):

    def test_init(self):
        path = "/test/path"
        rep = app.init_repo(path)

        self.assertEqual(rep.connector.url.path, path)
        self.assertEqual(rep.index, index.PictureIndex())
        self.assertEqual(rep.config, repo.new_repo_config())


@mock.patch('app.Connector', new=MockConnector)
class LoadRepoTest(unittest.TestCase):

    def test_load(self):
        path = "/test/path"
        rep_saved = new_mock_repo(path, num_pics=11)
        rep_loaded = app.load_repo(path)

        self.assertEqual(rep_loaded.connector.url.path, path)
        self.assertEqual(rep_loaded.index, rep_saved.index)
        self.assertEqual(rep_loaded.config, rep_saved.config)


@mock.patch('app.Connector', new=MockConnector)
class AddRemovePicsTest(unittest.TestCase):

    def setUp(self):
        self.path = "/testpath/to/repo"
        self.connector = MockConnector.from_string(self.path)

    @mock.patch('os.path.exists')
    def test_add_to_empty_repo(self, mock_exists):
        rep = new_mock_repo(self.path, num_pics=0)  # new empty repo
        pics = ['DSC_%04i' % i for i in range(15)]  # pictures to be added
        rep = app.add_pics(rep, pics, process=False)

        for pic in pics:
            self.assertIn(pic, rep.index)
        self.assertEqual(len(rep.index), len(pics))

    @mock.patch('os.path.exists')
    def test_append_to_repo(self, mock_exists):
        rep = new_mock_repo(self.path, num_pics=11)  # new preloaded reppo
        old_pics = [pic.filename for pic in rep.index.iterpics()]
        new_pics = ['DSC_%04i' % i for i in range(5)]  # pictures to be added
        rep = app.add_pics(rep, new_pics, process=False)

        for pic in new_pics:
            self.assertIn(pic, rep.index)
        for pic in old_pics:
            self.assertIn(pic, rep.index)
        self.assertEqual(len(rep.index), len(old_pics) + len(new_pics))

    def test_remove_pics(self):
        rep = new_mock_repo(self.path, num_pics=25)
        keep = [pic.filename for pic in rep.index.pics()[::2]]  # 0,2,4,6,... 
        remove = [pic.filename for pic in rep.index.pics()[1::2]]  # 1,3,5,7,...
        rep = app.remove_pics(rep, remove)

        for pic in remove:
            self.assertNotIn(pic, rep.index)
            self.assertTrue(self.connector.removed(pic))
        for pic in keep:
            self.assertIn(pic, rep.index)
            self.assertFalse(self.connector.removed(pic))
        self.assertEqual(len(rep.index), len(keep))


@mock.patch('app.Connector', new=MockConnector)
class ListPicsTests(unittest.TestCase):

    def setUp(self):
        self.repo = new_mock_repo("test/path", num_pics=13)

    def test_list_all(self):
        template = "%s\n  Sidecar files:\n   thumbnail: %s"
        expected = '\n'.join([template % (pic.filename,
                                          pic.get_thumbnail_filenames()[0])
                              for pic in self.repo.index.pics()])
        actual = app.list_pics(self.repo, 'all')
        self.assertEqual(actual, expected)

    def test_list_thumbnails(self):
        expected = '\n'.join(['\n'.join(pic.get_thumbnail_filenames())
                              for pic in self.repo.index.pics()])
        actual = app.list_pics(self.repo, 'thumbnails')
        self.assertEqual(actual, expected)

    def test_list_sidecars(self):
        expected = '\n'.join(['\n'.join(pic.get_sidecar_filenames())
                              for pic in self.repo.index.pics()])
        actual = app.list_pics(self.repo, 'sidecars')
        self.assertEqual(actual, expected)

    def test_list_checksums(self):
        expected = '\n'.join(['%s *%s' % (pic.checksum, pic.filename)
                              for pic in self.repo.index.pics()])
        actual = app.list_pics(self.repo, 'checksums')
        self.assertEqual(actual, expected)


@mock.patch('app.remove_pics')
@mock.patch('app.Viewer', spec_set=True)
class ViewPicsTests(unittest.TestCase):

    def setUp(self):
        path = '/basedir/repo/'
        self.repo = new_mock_repo(path, num_pics=31)

    def test_default_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        app.view_pics(self.repo, prog=None)

        MockViewer.assert_called_once_with(self.repo.config['viewer.prog'])
        mock_viewer_inst.show.assert_called_once_with(self.repo.index.pics())
        mock_remove_pics.assert_called_once_with(self.repo, [])

    def test_supplied_prog(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = []

        prog = 'awesome-viewer-app arg1 --opt1 -o2'
        app.view_pics(self.repo, prog)

        MockViewer.assert_called_once_with(prog)
        mock_viewer_inst.show.assert_called_once_with(self.repo.index.pics())
        mock_remove_pics.assert_called_once_with(self.repo, [])

    def test_removing_pics(self, MockViewer, mock_remove_pics):
        mock_viewer_inst = MockViewer.return_value
        mock_viewer_inst.show.return_value = self.repo.index.pics()[4:7]

        app.view_pics(self.repo, prog=None)

        pic_filenames = [pic.filename for pic in self.repo.index.pics()[4:7]]
        mock_remove_pics.assert_called_with(self.repo, pic_filenames)


@mock.patch('app.Connector', new=MockConnector)
class MigrateRepoTests(unittest.TestCase):

    def test_migrate_repo(self):
        path = '/basedir/repo/'
        repo_old = new_mock_repo(path, num_pics=10)
        repo_old.config['index.format_version'] = 0
        with MockConnector.from_string(path).connected():
            repo_old.save_config_to_disk()
        repo_new = app.migrate_repo(repo_old)

        self.assertEqual(repo_new.config['index.format_version'],
                         repo.INDEX_FORMAT_VERSION)#


@mock.patch('app.Connector', new=MockConnector)
class CheckPicsTests(unittest.TestCase):

    def populate_picture_buffers(self, repository):
        """Write pic's filename into its buffer because checksums = filename."""
        with repository.connector.connected():
            for pic in repository.index.iterpics():
                with repository.connector.open(pic.filename, 'w') as buf:
                    buf.write(pic.filename)
        return repository

    def test_empty_repo(self):
        empty_repo = new_mock_repo('/basedir/repo/', num_pics=0)

        corrupt, missing = app.check_pics(empty_repo)

        self.assertSequenceEqual(corrupt, [])
        self.assertSequenceEqual(missing, [])

    def test_all_ok(self):
        rep = new_mock_repo('/basedir/repo/', num_pics=10)
        rep = self.populate_picture_buffers(rep)

        corrupt, missing = app.check_pics(rep)

        self.assertSequenceEqual(corrupt, [])
        self.assertSequenceEqual(missing, [])

    def test_corrupted_pics(self):
        rep = new_mock_repo('/basedir/repo/', num_pics=31)
        rep = self.populate_picture_buffers(rep)
        corrupted = rep.index.pics()[::3]
        for pic in corrupted:
            pic.checksum = 'wrong checksum!'

        corrupt, missing = app.check_pics(rep)

        self.assertSequenceEqual(corrupt, [pic.filename for pic in corrupted])
        self.assertSequenceEqual(missing, [])

    def test_missing_pics(self):
        rep = new_mock_repo('/path/to/missingpics/repo', num_pics=31)
        def raise_oserror(*args):
            raise OSError
        rep.connector.open = raise_oserror

        corrupt, missing = app.check_pics(rep)

        self.assertSequenceEqual(corrupt, [])
        self.assertSequenceEqual(missing, [pic.filename
                                           for pic in rep.index.pics()])


@mock.patch('app.Connector', new=MockConnector)
class MergeReposTests(unittest.TestCase):

    def test_merge_repos(self):
        target = new_mock_repo('/target/repo', num_pics=14)

        pathA = '/other/repoA'
        repoA = new_mock_repo(pathA, num_pics=2)
        pathB = '/other/repoB'
        repoB = new_mock_repo(pathB, num_pics=26)

        target = app.merge_repos(target, pathA, pathB)

        for pic in repoA.index.iterpics():
            self.assertIn(pic, target.index.pics())
        for pic in repoB.index.iterpics():
            self.assertIn(pic, target.index.pics())
        self.assertEqual(len(target.index), 42)


@mock.patch('app.Connector', new=MockConnector)
class CloneRepoTests(unittest.TestCase):

    def setUp(self):
        self.origin_path = '/orig/path/foorepo'
        self.origin = new_mock_repo(self.origin_path, num_pics=17)
        self.clone_basepath = '/clone/path'
        self.clone_path = os.path.join(self.clone_basepath, 'foorepo')

    def test_clone_repo(self):
        clone = app.clone_repo(self.origin_path, self.clone_basepath)

        self.assertEqual(clone.config, self.origin.config)
        self.assertEqual(clone.index, self.origin.index)

    def test_cloned_repo_path(self):
        clone = app.clone_repo(self.origin_path, self.clone_basepath)

        self.assertEqual(clone.connector.url.path, self.clone_path,
                         "Path to clone should be basepath + repo-name.")

    def test_cloned_repo_exists_on_disk(self):
        clone = app.clone_repo(self.origin_path, self.clone_basepath)

        with clone.connector.connected():
            clone_on_disk = repo.Repo.load_from_disk(clone.connector)

        self.assertEqual(clone_on_disk.config, self.origin.config)
        self.assertEqual(clone_on_disk.index, self.origin.index)


@mock.patch('app.Connector', new=MockConnector)
class BackupRepoTests(unittest.TestCase):

    def setUp(self):
        self.repo = new_mock_repo('/repo/path/')

        self.backupA_path = '/backupA'
        self.backupB_path = '/backupB'

    def test_backup_repo(self):
        (backup,) = app.backup_repo(self.repo, self.backupA_path)

        self.assertEqual(backup.config, self.repo.config)
        self.assertEqual(backup.index, self.repo.index)

    def test_backed_up_repo_exists_on_disk(self):
        (backup,) = app.backup_repo(self.repo, self.backupA_path)

        with backup.connector.connected():
            backup_on_disk = repo.Repo.load_from_disk(backup.connector)

        self.assertEqual(backup_on_disk.config, backup.config)
        self.assertEqual(backup_on_disk.index, backup.index)

    def test_backup_repo_many(self):
        backups = app.backup_repo(self.repo,
                                  self.backupA_path, self.backupB_path)

        for backup in backups:
            self.assertEqual(backup.config, self.repo.config)
            self.assertEqual(backup.index, self.repo.index)


if __name__ == "__main__":
    unittest.main()
