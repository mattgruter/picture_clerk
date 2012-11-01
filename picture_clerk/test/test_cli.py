"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import os

from cli import CLI
from testlib import suppress_stderr


class ArgsParsingTests(unittest.TestCase):

    def test_help(self):
        with self.assertRaises(SystemExit) as cm:
            CLI().main(['progname', '--help'])
        self.assertEqual(cm.exception.code, 0, "Expected exit code == 0")

    def test_missing_args(self):
        with suppress_stderr():
            with self.assertRaises(SystemExit) as cm:
                CLI().main(['progname'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")

    def test_unknown_args(self):
        with suppress_stderr():
            with self.assertRaises(SystemExit) as cm:
                CLI().main(['progname', 'asdf'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")


class CLIBaseTest(unittest.TestCase):

    def create_patch(self, name):
        patcher = mock.patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def setUp(self):
        self.cwd = os.path.abspath('.')

        self.mock_sys_exit = self.create_patch('sys.exit')
        self.mock_init_repo = self.create_patch('app.init_repo')
        self.mock_load_repo = self.create_patch('app.load_repo')
        self.mock_add_pics = self.create_patch('app.add_pics')
        self.mock_remove_pics = self.create_patch('app.remove_pics')
        self.mock_list_pics = self.create_patch('app.list_pics')
        self.mock_view_pics = self.create_patch('app.view_pics')
        self.mock_migrate_repo = self.create_patch('app.migrate_repo')
        self.mock_check_pics = self.create_patch('app.check_pics')
        self.mock_merge_repos = self.create_patch('app.merge_repos')
        self.mock_clone_repo = self.create_patch('app.clone_repo')
        self.mock_backup_repo = self.create_patch('app.backup_repo')
        self.mock_app_shutdown = self.create_patch('app.shutdown')


class BasicTests(CLIBaseTest):

    def test_main(self):
        CLI().main(['progname', 'init'])
        self.mock_app_shutdown.assert_called_once_with()
        self.mock_sys_exit.assert_called_once_with(0)  # error-free exit

    def test_shutdown(self):
        CLI().shutdown(17)
        self.mock_app_shutdown.assert_called_once_with()
        self.mock_sys_exit.assert_called_once_with(17)


class InitTests(CLIBaseTest):

    def test_init(self):
        CLI().main(['progname', 'init'])

        self.mock_init_repo.assert_called_once_with(self.cwd)
        self.mock_sys_exit.assert_called_once_with(0)


class AddTests(CLIBaseTest):

    def test_add(self):
        files = ['file1', 'file2', 'file3']
        CLI().main(['progname', 'add'] + files)

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_add_pics.assert_called_once_with(repo, files, True, None)
        self.mock_sys_exit.assert_called_once_with(0)

    def test_add_without_processing(self):
        files = ['file1', 'file2', 'file3']
        CLI().main(['progname', 'add'] + files + ['--noprocess'])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_add_pics.assert_called_once_with(repo, files, False, None)
        self.mock_sys_exit.assert_called_once_with(0)

    def test_add_with_process_recipe(self):
        files = ['file1', 'file2', 'file3']
        recipe = 'FOO.BAR'
        CLI().main(['progname', 'add'] + files + ['--recipe', recipe])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_add_pics.assert_called_once_with(repo, files, True, recipe)
        self.mock_sys_exit.assert_called_once_with(0)


class RemoveTests(CLIBaseTest):

    def test_remove(self):
        files = ['file1', 'file2', 'file3']
        CLI().main(['progname', 'remove'] + files)

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_remove_pics.assert_called_once_with(repo, files)
        self.mock_sys_exit.assert_called_once_with(0)


class ListTests(CLIBaseTest):

    def test_list_default(self):
        CLI().main(['progname', 'list'])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_list_pics.assert_called_once_with(repo, 'all')
        self.mock_sys_exit.assert_called_once_with(0)

    def test_list_modes(self):
        repo = self.mock_load_repo.return_value
        for mode in ['all', 'thumbnails', 'sidecars', 'checksums']:
            self.mock_load_repo.reset_mock()
            self.mock_list_pics.reset_mock()
            self.mock_sys_exit.reset_mock()

            CLI().main(['progname', 'list', mode])

            self.mock_load_repo.assert_called_once_with(self.cwd)
            repo = self.mock_load_repo.return_value
            self.mock_list_pics.assert_called_once_with(repo, mode)
            self.mock_sys_exit.assert_called_once_with(0)


class ViewTests(CLIBaseTest):

    def test_default_viewer(self):
        CLI().main(['progname', 'view'])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_view_pics.assert_called_once_with(repo, None)
        self.mock_sys_exit.assert_called_once_with(0)

    def test_supplied_viewer(self):
        prog = 'fooview fooviewarg --fooviewopt'
        CLI().main(['progname', 'view', '--viewer', prog])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_view_pics.assert_called_once_with(repo, prog)
        self.mock_sys_exit.assert_called_once_with(0)


class MigrateTests(CLIBaseTest):

    def test_migrate(self):
        CLI().main(['progname', 'migrate'])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_migrate_repo.assert_called_once_with(repo)
        self.mock_sys_exit.assert_called_once_with(0)


class CheckTests(CLIBaseTest):

    def test_check(self):
        self.mock_check_pics.return_value = ([], [])
        CLI().main(['progname', 'check'])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_check_pics.assert_called_once_with(repo)
        self.mock_sys_exit.assert_called_once_with(0)

    def test_check_fail(self):
        self.mock_check_pics.return_value = (['corrupt pic'], ['missing pic'])
        CLI().main(['progname', 'check'])

        self.mock_sys_exit.assert_called_once_with(1)


class MergeTests(CLIBaseTest):

    def test_merge(self):
        others = ['repoA', 'repoB', 'repoC']
        CLI().main(['progname', 'merge'] + others)

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_merge_repos.assert_called_once_with(repo, *others)
        self.mock_sys_exit.assert_called_once_with(0)


class CloneTests(CLIBaseTest):

    def test_clone(self):
        src_url = "/origin/url"
        CLI().main(['progname', 'clone', src_url])

        self.mock_clone_repo.assert_called_once_with(src=src_url, dest=self.cwd)
        self.mock_sys_exit.assert_called_once_with(0)


class BackupTests(CLIBaseTest):

    def test_backup(self):
        backup_url = '/backup/url'
        CLI().main(['progname', 'backup', backup_url])

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_backup_repo.assert_called_once_with(repo, backup_url)
        self.mock_sys_exit.assert_called_once_with(0)

    def test_backup_to_many(self):
        backup_urls = ['/backup1/url', '/backup2/url', '/backup3/url']
        CLI().main(['progname', 'backup'] + backup_urls)

        self.mock_load_repo.assert_called_once_with(self.cwd)
        repo = self.mock_load_repo.return_value
        self.mock_backup_repo.assert_called_once_with(repo, *backup_urls)
        self.mock_sys_exit.assert_called_once_with(0)

    @unittest.skip("not implemented yet")
    def test_backup_to_default(self, MockConnector, mock_app, mock_exit):
        """ 'backup' without argument should use default urls in config. """
        pass


if __name__ == "__main__":
    unittest.main()
