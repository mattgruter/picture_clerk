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

from app import App
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
        formatter = logging.Formatter('%(message)s')

        # stdout console logger
        log_level = logging.WARNING  # default
        if verbosity == 1:
            log_level = logging.INFO
        elif verbosity >= 2:
            log_level = logging.DEBUG
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(log_level)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def dispatch_args(self, app, args):
        return args.func(app, args)

    def handle_init_cmd(self, app, args):
        app.init_repo()
        return 0

    def handle_add_cmd(self, app, args):
        app.load_repo()
        app.add_pics(args.files, args.process, args.recipe)
        return 0

    def handle_remove_cmd(self, app, args):
        app.load_repo()
        app.remove_pics(args.files)
        return 0

    def handle_list_cmd(self, app, args):
        app.load_repo()
        print app.list_pics(args.mode)
        return 0

    def handle_view_cmd(self, app, args):
        app.load_repo()
        app.view_pics(args.viewer)
        return 0

    def handle_migrate_cmd(self, app, args):
        app.load_repo()
        app.migrate_repo()
        return 0

    def handle_test_cmd(self, app, args):
        print "Testing..."
        log.info("Starting endless loop.")
        while True:
            pass
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
            help="remove pictures from repository")
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

        # 'test' subcommand
        parser_test = subparsers.add_parser(
            'test',
            help="testing CLI")
        parser_test.set_defaults(func=self.handle_test_cmd)

        return parser.parse_args(args)

    def main(self, argv):
        args = self.parse_args(argv[1:])
        self.setup_signal_handlers()
        self.setup_logging(args.verbosity)
        self.app = App(Connector.from_string('.'))
        exit_code = self.dispatch_args(self.app, args)
        self.shutdown(exit_code)

    def shutdown(self, exit_code):
        self.app.shutdown()
        logging.shutdown()
        sys.exit(exit_code)


if __name__ == "__main__":
    CLI().main(sys.argv)
