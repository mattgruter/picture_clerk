"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock
import os

from cli import CLI
from connector import Connector
from testlib import suppress_stderr


@mock.patch('sys.exit')
class BasicTests(unittest.TestCase):

    @mock.patch('app.init_repo')
    def test_main(self, mock_init, mock_exit):
        CLI().main(['progname', 'init'])
        mock_exit.assert_called_once_with(0)        # error-free exit

    def test_shutdown(self, mock_exit):
        CLI().shutdown(17)
        mock_exit.assert_called_once_with(17)


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


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandInitTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_init(self, mock_app, mock_exit):
        CLI().main(['progname', 'init'])

        mock_app.init_repo.assert_called_once_with(self.cwd)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandAddTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_add(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'add'] + self.files)

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.add_pics.assert_called_once_with(repo, self.files, True, None)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_without_processing(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'add'] + self.files + ['--noprocess'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.add_pics.assert_called_once_with(repo, self.files, False, None)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_with_process_recipe(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'add'] + self.files + ['--recipe', 'FOO,BAR'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.add_pics.assert_called_once_with(repo, self.files,
                                                  True, 'FOO,BAR')
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandRemoveTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_remove(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'remove'] + self.files)

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.remove_pics.assert_called_once_with(repo, self.files)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandListTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_list_default(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'list'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.list_pics.assert_called_once_with(repo, 'all')
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_list_modes(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value
        for mode in ['all', 'thumbnails', 'sidecars', 'checksums']:
            mock_app.reset_mock()
            mock_exit.reset_mock()

            CLI().main(['progname', 'list', mode])

            mock_app.load_repo.assert_called_once_with(self.cwd)
            mock_app.list_pics.assert_called_once_with(repo, mode)
            mock_app.shutdown.assert_called_once_with()
            mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandViewTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_default_viewer(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'view'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.view_pics.assert_called_once_with(repo, None)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_supplied_viewer(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value
        prog = 'fooview fooviewarg --fooviewopt'

        CLI().main(['progname', 'view', '--viewer', prog])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.view_pics.assert_called_once_with(repo, prog)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandMigrateTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_migrate(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'migrate'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.migrate_repo.assert_called_once_with(repo)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandCheckTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_check(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value
        mock_app.check_pics.return_value = ([], [])

        CLI().main(['progname', 'check'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.check_pics.assert_called_once_with(repo)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_check_fail(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value
        mock_app.check_pics.return_value = (['corrupt pic'], ['missing pic'])

        CLI().main(['progname', 'check'])

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.check_pics.assert_called_once_with(repo)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(1)

@mock.patch('sys.exit')
@mock.patch('cli.app')
class SubcommandMergeTests(unittest.TestCase):

    def setUp(self):
        self.repos = ['repoA', 'repoB', 'repoC']
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_merge(self, mock_app, mock_exit):
        repo = mock_app.load_repo.return_value

        CLI().main(['progname', 'merge'] + self.repos)

        mock_app.load_repo.assert_called_once_with(self.cwd)
        mock_app.merge_repos.assert_called_once_with(repo, self.repos)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

@mock.patch('sys.exit')
@mock.patch('cli.app')
@mock.patch('cli.Connector', spec_set=Connector)
class SubcommandCloneTests(unittest.TestCase):

    def setUp(self):
        self.cwd = Connector.from_string(os.path.abspath('.'))

    def test_clone(self, MockConnector, mock_app, mock_exit):
        src_url = "/origin/url"

        CLI().main(['progname', 'clone', src_url])

        src = MockConnector.from_string(src_url)
        dest = MockConnector.from_string('.')
        mock_app.clone_repo.assert_called_once_with(src, dest)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

@mock.patch('sys.exit')
@mock.patch('cli.app')
@mock.patch('cli.Connector', spec_set=Connector)
class BackupTests(unittest.TestCase):

    def test_backup(self, MockConnector, mock_app, mock_exit):
        cwd = MockConnector.from_string('.')
        repo = mock_app.load_repo.return_value
        backup_url = "/backup/url"
        backup_connector = MockConnector.from_string(backup_url)

        CLI().main(['progname', 'backup', backup_url])

        mock_app.load_repo.assert_called_once_with(cwd)
        mock_app.backup_repo.assert_called_once_with(repo, backup_connector)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_backup_to_many_urls(self, MockConnector, mock_app, mock_exit):
        cwd = MockConnector.from_string('.')
        repo = mock_app.load_repo.return_value
        backup_urls = ["url1", "url2", "url3"]
        backup_connectors = [ MockConnector.from_string(url)
                             for url in backup_urls ]

        CLI().main(['progname', 'backup'] + backup_urls)

        mock_app.load_repo.assert_called_once_with(cwd)
        mock_app.backup_repo.assert_called_once_with(repo, *backup_connectors)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    @unittest.skip("not implemented yet")
    def test_backup_to_default(self, MockConnector, mock_app, mock_exit):
        """ 'backup' without argument should use default urls in config. """
        cwd = MockConnector.from_string('.')
        repo = mock_app.load_repo.return_value
        default_backup_urls = ["url1", "url2", "url3"]
        default_backup_connectors = [ MockConnector.from_string(url)
                                     for url in default_backup_urls ]

        CLI().main(['progname', 'backup'])

        mock_app.load_repo.assert_called_once_with(cwd)
        mock_app.backup_repo.assert_called_once_with(repo,
                                                     *default_backup_connectors)
        mock_app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
