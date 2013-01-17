#!/usr/bin/env python
"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import logging
import argparse
import signal
import sys
import os
import pprint

import app
import config


log = logging.getLogger('pic.cli')


class CLI(object):
    """PictureClerk's command line interface."""

    def __init__(self):
        self.app = None

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def handle_sigint(self, signum, frame):
        print("Caught signal INT")  # don't use logging due to possible deadlock
        self.shutdown(exit_code=128 + signum)

    def handle_sigterm(self, signum, frame):
        print("Caught signal TERM")  # don't use logging due to possible deadlock
        self.shutdown(exit_code=128 + signum)

    def setup_logging(self, verbosity):
        """Configure logging and add console logger with supplied verbosity.

        Arguments:
        verbosity -- console loglevel (0 -> warning, 1 -> info, 2 -> debug)

        """
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # stdout console logger
        formatter = logging.Formatter('%(message)s')
        log_level = logging.WARNING  # default
        if verbosity == 1:
            log_level = logging.INFO
        elif verbosity >= 2:
            log_level = logging.DEBUG
            formatter = logging.Formatter("%(asctime)s "
                                          "%(name)-15s"
                                          "%(levelname)-8s "
                                          "%(message)s")
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(log_level)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def handle_command(self, conf):
        log.info("Configuration:\n%s", pprint.pformat(conf))
        try:
            exit_code = conf['func'](conf)
        except:
            log.error("", exc_info=sys.exc_info())
            exit_code = 1
        return exit_code

    def handle_init_cmd(self, conf):
        app.init_repo(conf['working_dir'])
        return 0

    def handle_add_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.add_pics(repo, conf['add.files'], conf['add.process'], conf['add.recipe'])
        return 0

    def handle_remove_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.remove_pics(repo, conf['remove.files'])
        return 0

    def handle_list_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        print app.list_pics(repo, conf['list.mode'])
        return 0

    def handle_view_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.view_pics(repo, conf['viewer.prog'])
        return 0

    def handle_migrate_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.migrate_repo(repo)
        return 0

    def handle_check_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        corrupt_pics, missing_pics = app.check_pics(repo)
        exit_code = 0
        if corrupt_pics:
            print '\n'.join('CORRUPT: %s' % pic for pic in corrupt_pics)
            exit_code = 1
        if missing_pics:
            print '\n'.join('MISSING: %s' % pic for pic in missing_pics)
            exit_code = 1
        return exit_code

    def handle_merge_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.merge_repos(repo, *conf['merge.repos'])
        return 0

    def handle_clone_cmd(self, conf):
        app.clone_repo(src=conf['clone.repo'], dest=conf['working_dir'])
        return 0

    def handle_backup_cmd(self, conf):
        repo = app.load_repo(conf['working_dir'])
        app.backup_repo(repo, *conf['backup.path'])
        return 0

    def parse_args(self, args, conf):
        """Parse command line arguments and and return dict with args.

        Arguments:
        args -- list of command line arguments (e.g. sys.argv[1:])

        """
        descr = "PictureClerk - The little helper for your picture workflow."
        parser = argparse.ArgumentParser(description=descr, prog='pic')
        subparsers = parser.add_subparsers(title='commands', dest='cmd')

        # global arguments
        parser.add_argument(
            '-v', '--verbose',
            dest='logging.verbosity',
            action='count',
            help="more verbose output (can be supplied multiple times)")

        # 'init' subcommand
        parser_init = subparsers.add_parser(
            'init',
            help="initialize empty repository")
        parser_init.set_defaults(func=self.handle_init_cmd)

        # 'add' subcommand
        parser_add = subparsers.add_parser(
            'add',
            help="add picture files to repository")
        parser_add.add_argument(
            '-n', '--noprocess',
            dest='add.process',
            default=True,
            action='store_false',
            help="only add files to repository without processing")
        parser_add.add_argument(
            '--recipe',
            dest='add.recipe',
            metavar='RECIPE',
            help="processing instructions (comma separated list)")
        parser_add.add_argument(
            'add.files',
            metavar='file',
            nargs='+',
            help="picture file(s) to add")
        parser_add.set_defaults(func=self.handle_add_cmd)

        # 'remove' subcommand
        parser_remove = subparsers.add_parser(
            'remove',
            help="remove pictures and associated files")
        parser_remove.add_argument(
            'remove.files',
            metavar='file',
            nargs='+',
            help="picture(s) to remove")
        parser_remove.set_defaults(func=self.handle_remove_cmd)

        # 'list' subcommand
        parser_list = subparsers.add_parser(
            'list',
            help="print information about repository")
        parser_list.add_argument(
            'list.mode',
            nargs='?',
            default='all',
            choices=['all', 'thumbnails', 'sidecars', 'checksums'],
            help="type of information to print (default: 'all')")
        parser_list.set_defaults(func=self.handle_list_cmd)

        # 'view' subcommand
        parser_view = subparsers.add_parser(
            'view',
            help="view pictures")
        parser_view.add_argument(
             '--viewer',
             dest='viewer.prog',
             metavar='CMD',
             help="program to use as picture viewer")
        parser_view.set_defaults(func=self.handle_view_cmd)

        # 'migrate' subcommand
        parser_migrate = subparsers.add_parser(
            'migrate',
            help="migrate repository to new format")
        parser_migrate.set_defaults(func=self.handle_migrate_cmd)

        # 'check' subcommand
        parser_check = subparsers.add_parser(
            'check',
            help="find corrupt or missing picture files")
        parser_check.set_defaults(func=self.handle_check_cmd)

        # 'merge' subcommand
        parser_merge = subparsers.add_parser(
            'merge',
            help="join two or more repositories together")
        parser_merge.add_argument(
            'merge.repos',
            metavar='repo',
            nargs='+',
            help="repositories to merge into current one")
        parser_merge.set_defaults(func=self.handle_merge_cmd)

        # 'clone' subcommand
        parser_clone = subparsers.add_parser(
            'clone',
            help="clone repository")
        parser_clone.add_argument(
            'clone.repo',
            metavar='repo',
            help="repository to clone (origin)")
        parser_clone.set_defaults(func=self.handle_clone_cmd)

        # 'backup' subcommand
        try:
            backup_paths = [os.path.expanduser(path)
                            for path in conf['backup.path'].split(':')]
        except KeyError:
            backup_paths = None
        parser_backup = subparsers.add_parser(
            'backup',
            help="backup repository")
        parser_backup.add_argument(
            'backup.path',
            default=backup_paths,
            metavar='path',
            nargs='*',
            help="one or more backup path(s)")
        parser_backup.set_defaults(func=self.handle_backup_cmd)

        return vars(parser.parse_args(args))

    def load_config(self):
        conf = config.new_app_config()
        try:
            with open(config.APP_CONFIG_FILE, 'r') as config_fh:
                conf.read(config_fh)
        except IOError:
            pass
        return conf

    def merge_args_into_config(self, conf, args):
        merged = conf.todict()
        merged.update(args)
        return merged

    def main(self, argv):
        conf = self.load_config()
        args = self.parse_args(argv[1:], conf)
        conf = self.merge_args_into_config(conf, args)
        conf['working_dir'] = os.path.abspath('.')

        self.setup_signal_handlers()
        self.setup_logging(conf['logging.verbosity'])

        exit_code = self.handle_command(conf)
        self.shutdown(exit_code)

    def shutdown(self, exit_code):
        app.shutdown()
        logging.shutdown()
        sys.exit(exit_code)


if __name__ == "__main__":
    CLI().main(sys.argv)
