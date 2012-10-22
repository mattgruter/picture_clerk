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

import app

from connector import Connector


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
        print("Caught signal TERM") # don't use logging due to possible deadlock
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

    def dispatch_args(self, args, cwd):
        try:
            exit_code = args.func(args, cwd)
        except:
            log.info("", exc_info=sys.exc_info())
            log.error(sys.exc_info()[1])
            exit_code = 1
        return exit_code

    def handle_init_cmd(self, args, cwd):
        app.init_repo(cwd)
        return 0

    def handle_add_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        app.add_pics(repo, args.files, args.process, args.recipe)
        return 0

    def handle_remove_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        app.remove_pics(repo, args.files)
        return 0

    def handle_list_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        print app.list_pics(repo, args.mode)
        return 0

    def handle_view_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        app.view_pics(repo, args.viewer)
        return 0

    def handle_migrate_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        app.migrate_repo(repo)
        return 0

    def handle_check_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        corrupt_pics, missing_pics = app.check_pics(repo)
        exit_code = 0
        if corrupt_pics:
            print '\n'.join('CORRUPT: %s' % pic for pic in corrupt_pics)
            exit_code = 1
        if missing_pics:
            print '\n'.join('MISSING: %s' % pic for pic in missing_pics)
            exit_code = 1
        return exit_code

    def handle_merge_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        app.merge_repos(repo, args.repos)
        return 0

    def handle_clone_cmd(self, args, cwd):
        src = Connector.from_string(args.repo)
        try:
            src.connect()
            app.clone_repo(src, cwd)
        finally:
            src.disconnect()
        return 0

    def handle_backup_cmd(self, args, cwd):
        repo = app.load_repo(cwd)
        connectors = [Connector.from_string(location)
                      for location in args.locations]
        try:
            for connector in connectors:
                connector.connect()
            app.backup_repo(repo, *connectors)
        finally:
            for connector in connectors:
                connector.disconnect()
        return 0

    def parse_args(self, args):
        """Parse command line arguments and return result.
        
        Arguments:
        args -- list of command line arguments (e.g. sys.argv[1:])
        
        """
        descr = "PictureClerk - The little helper for your picture workflow."
        parser = argparse.ArgumentParser(description=descr)
        subparsers = parser.add_subparsers(title='commands', dest='cmd')

        # global arguments
        parser.add_argument(
            '-v', '--verbose',
            dest='verbosity',
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
            dest='process',
            default=True,
            action='store_false',
            help="only add files to repository without processing")
        parser_add.add_argument(
            '--recipe',
            dest='recipe',
            help="processing instructions (comma separated list)")
        parser_add.add_argument(
            'files',
            metavar='file',
            nargs='+',
            help="picture file(s) to add")
        parser_add.set_defaults(func=self.handle_add_cmd)

        # 'remove' subcommand
        parser_remove = subparsers.add_parser(
            'remove',
            help="remove pictures and associated files")
        parser_remove.add_argument(
            'files',
            metavar='file',
            nargs='+',
            help="picture(s) to remove")
        parser_remove.set_defaults(func=self.handle_remove_cmd)

        # 'list' subcommand
        parser_list = subparsers.add_parser(
            'list',
            help="print information about repository")
        parser_list.add_argument(
            'mode',
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
            'repos',
            metavar='repo',
            nargs='+',
            help="repositories to merge into current one")
        parser_merge.set_defaults(func=self.handle_merge_cmd)

        # 'clone' subcommand
        parser_clone = subparsers.add_parser(
            'clone',
            help="clone repository")
        parser_clone.add_argument(
            'repo',
            metavar='repo',
            help="repository to clone (origin)")
        parser_clone.set_defaults(func=self.handle_clone_cmd)

        # 'backup' subcommand
        parser_backup = subparsers.add_parser(
            'backup',
            help="backup repository")
        parser_backup.add_argument(
            'locations',
            nargs='*',
            metavar='locations',
            help="one or more backup location(s)")
        parser_backup.set_defaults(func=self.handle_backup_cmd)

        return parser.parse_args(args)

    def main(self, argv):
        args = self.parse_args(argv[1:])
        self.setup_signal_handlers()
        self.setup_logging(args.verbosity)
        connector = Connector.from_string(os.path.abspath('.'))
        try:
            connector.connect()
            exit_code = self.dispatch_args(args, cwd=connector)
        finally:
            connector.disconnect()
        self.shutdown(exit_code)

    def shutdown(self, exit_code):
        app.shutdown()
        logging.shutdown()
        sys.exit(exit_code)


if __name__ == "__main__":
    CLI().main(sys.argv)
