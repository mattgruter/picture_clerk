"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL
"""
import unittest
import mock

from cli import CLI


@mock.patch('sys.exit')
@mock.patch('cli.App')
class BasicTests(unittest.TestCase):

    def test_main(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'init'])
        self.assertEqual(cli.app, app)
        mock_exit.assert_called_once_with(0)        # error-free exit

    def test_shutdown(self, MockApp, mock_exit):
        cli = CLI()
        cli.app = MockApp()
        cli.shutdown(17)
        mock_exit.assert_called_once_with(17)


@mock.patch('cli.App')
class ArgsParsingTests(unittest.TestCase):

    def test_help(self, MockApp):
        cli = CLI()
        with self.assertRaises(SystemExit) as cm:
            cli.main(['progname', '--help'])
        self.assertEqual(cm.exception.code, 0, "Expected exit code == 0")

    def test_missing_args(self, MockApp):
        cli = CLI()
        with self.assertRaises(SystemExit) as cm:
            cli.main(['progname'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")

    def test_unknown_args(self, MockApp):
        cli = CLI()
        with self.assertRaises(SystemExit) as cm:
            cli.main(['progname', 'asdf'])
        self.assertNotEqual(cm.exception.code, 0, "Expected non-zero exit code")


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandInitTests(unittest.TestCase):

    def test_init(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'init'])

        app.init_repo.assert_called_once_with()
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandAddTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']

    def test_add(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'add'] + self.files)

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(self.files, True, None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_without_processing(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'add'] + self.files + ['--noprocess'])

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(self.files, False, None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_add_with_process_recipe(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'add'] + self.files + ['--recipe', 'FOO,BAR'])

        app.load_repo.assert_called_once_with()
        app.add_pics.assert_called_once_with(self.files, True, 'FOO,BAR')
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandRemoveTests(unittest.TestCase):

    def setUp(self):
        self.files = ['file1', 'file2', 'file3']

    def test_remove(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'remove'] + self.files)

        app.load_repo.assert_called_once_with()
        app.remove_pics.assert_called_once_with(self.files)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandListTests(unittest.TestCase):

    def test_list_default(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'list'])

        app.load_repo.assert_called_once_with()
        app.list_pics.assert_called_once_with('all')
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_list_modes(self, MockApp, mock_exit):
        app = MockApp()
        for mode in ['all', 'thumbnails', 'sidecars', 'checksums']:
            app.reset_mock()
            mock_exit.reset_mock()

            cli = CLI()
            cli.main(['progname', 'list', mode])

            app.load_repo.assert_called_once_with()
            app.list_pics.assert_called_once_with(mode)
            app.shutdown.assert_called_once_with()
            mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandViewTests(unittest.TestCase):

    def test_default_viewer(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'view'])

        app.load_repo.assert_called_once_with()
        app.view_pics.assert_called_once_with(None)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_supplied_viewer(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        prog = 'fooview fooviewarg --fooviewopt'
        cli.main(['progname', 'view', '--viewer', prog])

        app.load_repo.assert_called_once_with()
        app.view_pics.assert_called_once_with(prog)
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandMigrateTests(unittest.TestCase):

    def test_migrate(self, MockApp, mock_exit):
        app = MockApp()
        cli = CLI()
        cli.main(['progname', 'migrate'])

        app.load_repo.assert_called_once_with()
        app.migrate_repo.assert_called_once_with()
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)


@mock.patch('sys.exit')
@mock.patch('cli.App')
class SubcommandCheckTests(unittest.TestCase):

    def test_check(self, MockApp, mock_exit):
        app = MockApp()
        app.check_pics.return_value = ([], [])
        cli = CLI()
        cli.main(['progname', 'check'])

        app.load_repo.assert_called_once_with()
        app.check_pics.assert_called_once_with()
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(0)

    def test_check_fail(self, MockApp, mock_exit):
        app = MockApp()
        app.check_pics.return_value = (['corrupt pic'], ['missing pic'])
        cli = CLI()
        cli.main(['progname', 'check'])

        app.load_repo.assert_called_once_with()
        app.check_pics.assert_called_once_with()
        app.shutdown.assert_called_once_with()
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
