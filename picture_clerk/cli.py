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
        args.func(app, args)

    def handle_init_cmd(self, app, args):
        app.init()

    def handle_add_cmd(self, app, args):
        app.add_pics(args.files, args.process, args.recipe)

    def handle_remove_cmd(self, app, args):
        app.remove_pics(args.files)

    def handle_list_cmd(self, app, args):
        print app.list_pics(args.mode)

    def handle_test_cmd(self, app, args):
        print "Testing..."
        log.info("Starting endless loop.")
        while True:
            pass

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
            '--noprocess', '-n',
            dest='process',
            default=True,
            action='store_false',
            help="only add files to repository without processing")
        parser_add.add_argument(
            '--recipe', '-r',
            dest='recipe',
            nargs=1,
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
        self.dispatch_args(self.app, args)
        self.shutdown(0)

    def shutdown(self, exit_code):
        self.app.shutdown()
        logging.shutdown()
        sys.exit(exit_code)


if __name__ == "__main__":
    CLI().main(sys.argv)
