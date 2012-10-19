"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import unittest
import mock

from cli import CLI
from app import App
from connector import Connector
from testlib import suppress_stderr


@mock.patch('sys.exit')
class BasicTests(unittest.TestCase):

    @mock.patch('cli.App')
    def test_main(self, MockApp, mock_exit):
        cli = CLI()
        cli.main(['progname', 'init'])
        mock_exit.assert_called_once_with(0)        # error-free exit

    def test_shutdown(self, mock_exit):
        cli = CLI()
        cli.shutdown(17)
        mock_exit.assert_called_once_with(17)


@mock.patch('cli.App', spec_set=App)
class ArgsParsingTests(unittest.TestCase):

    def test_help(self, MockApp):
        cli = CLI()
        with self.assertRaises(SystemExit) as cm:
            cli.main(['progname', '--help'])
        self.assertEqual(cm.exception.code, 0, "Expected exit code == 0")

    def test_missing_args(self, MockApp):
        cli = CLI()
        with suppress_stderr():
            with self.assertRaises(SystemExit) as cm:
                cli.main(['progname'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")

    def test_unknown_args(self, MockApp):
        cli = CLI()
        with suppress_stderr():
            with self.assertRaises(SystemExit) as cm:
                cli.main(['progname', 'asdf'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandInitTests(unittest.TestCase):

    def test_init(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'init'])

        app.init_repo.assert_called_once_with()
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandAddTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']

    def test_add(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'add'] + self.files)

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(repo, self.files, True, None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_without_processing(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'add'] + self.files + ['--noprocess'])

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(repo, self.files, False, None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_with_process_recipe(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'add'] + self.files + ['--recipe', 'FOO,BAR'])

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(repo, self.files, True, 'FOO,BAR')
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandRemoveTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']

    def test_remove(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'remove'] + self.files)

        app.load_repo.assert_called_once_with()
        app.remove_pics.assert_called_once_with(repo, self.files)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandListTests(unittest.TestCase):

    def test_list_default(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'list'])

        app.load_repo.assert_called_once_with()
        app.list_pics.assert_called_once_with(repo, 'all')
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_list_modes(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        for mode in ['all', 'thumbnails', 'sidecars', 'checksums']:
            app.reset_mock()
            mock_exit.reset_mock()

            cli = CLI()
            cli.main(['progname', 'list', mode])

            app.load_repo.assert_called_once_with()
            app.list_pics.assert_called_once_with(repo, mode)
            app.shutdown.assert_called_once_with()
            mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandViewTests(unittest.TestCase):

    def test_default_viewer(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'view'])

        app.load_repo.assert_called_once_with()
        app.view_pics.assert_called_once_with(repo, None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_supplied_viewer(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        prog = 'fooview fooviewarg --fooviewopt'
        cli.main(['progname', 'view', '--viewer', prog])

        app.load_repo.assert_called_once_with()
        app.view_pics.assert_called_once_with(repo, prog)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandMigrateTests(unittest.TestCase):

    def test_migrate(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'migrate'])

        app.load_repo.assert_called_once_with()
        app.migrate_repo.assert_called_once_with(repo)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandCheckTests(unittest.TestCase):

    def test_check(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        app.check_pics.return_value = ([], [])
        cli = CLI()
        cli.main(['progname', 'check'])

        app.load_repo.assert_called_once_with()
        app.check_pics.assert_called_once_with(repo)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_check_fail(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        app.check_pics.return_value = (['corrupt pic'], ['missing pic'])
        cli = CLI()
        cli.main(['progname', 'check'])

        app.load_repo.assert_called_once_with()
        app.check_pics.assert_called_once_with(repo)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(1)

@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
class SubcommandMergeTests(unittest.TestCase):

    def setUp(self):
        self.repos = ['repoA', 'repoB', 'repoC']

    def test_merge(self, MockApp, mock_exit):
        app = MockApp()
        repo = app.load_repo.return_value
        cli = CLI()
        cli.main(['progname', 'merge'] + self.repos)

        app.load_repo.assert_called_once_with()
        app.merge_repos.assert_called_once_with(repo, self.repos)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
@mock.patch('cli.Connector', spec_set=Connector)
class SubcommandCloneTests(unittest.TestCase):

    def test_merge(self, MockConnector, MockApp, mock_exit):
        orig_url = "/origin/url"
        CLI().main(['progname', 'clone', orig_url])

        app = MockApp()
        orig_connector = MockConnector.from_string(orig_url)
        app.clone_repo.assert_called_once_with(orig_connector)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

@mock.patch('sys.exit')
@mock.patch('cli.App', spec_set=App)
@mock.patch('cli.Connector', spec_set=Connector)
class BackupTests(unittest.TestCase):

    def test_backup(self, MockConnector, MockApp, mock_exit):
        backup_url = "/backup/url"
        CLI().main(['progname', 'backup', backup_url])
        app = MockApp()
        repo = app.load_repo.return_value
        
        backup_connector = MockConnector.from_string(backup_url)
        app.backup_repo.assert_called_once_with(repo, backup_connector)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_backup_to_many_urls(self, MockConnector, MockApp, mock_exit):
        backup_urls = ["url1", "url2", "url3"]
        CLI().main(['progname', 'backup'] + backup_urls)
        app = MockApp()
        repo = app.load_repo.return_value

        app = MockApp()
        connectors = [ MockConnector.from_string(url) for url in backup_urls ]
        app.backup_repo.assert_called_once_with(repo, *connectors)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    @unittest.skip("not implemented yet")
    def test_backup_to_default(self, MockConnector, MockApp, mock_exit):
        """ 'backup' without argument should use default urls in config. """
        default_urls = ["url1", "url2", "url3"]
        CLI().main(['progname', 'backup'])

        app = MockApp()
        connectors = [ MockConnector.from_string(url) for url in default_urls ]
        app.backup_repo.assert_called_once_with(*connectors)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)




if __name__ == "__main__":
    unittest.main()
