#!/usr/bin/env python
"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import logging
import optparse
import signal
import sys

from app import App
from connector import Connector

log = logging.getLogger('pic.cli')

class CLI(object):
    """PictureClerk's command line interface."""

    def parse_command_line(self, args):
        """Parse command line (sys.argv) and return the parsed args & opts.
        
        Returns:
        cmd       -- PictureClerk command (e.g. init, add, list)
        args      -- CLI positional arguments (excluding cmd)
        verbosity -- the desired logging verbosity
        
        """
        usage = ("Usage: %prog [<options>] <command> [<args>]\n\n"
        "Commands:\n"
        "  init           create an empty repository\n"
        "  add <files>    add picture files to the repository\n"
        "  list <mode>    list pictures in repository\n\n"
        "List modes:\n"
        "  all (default)  print all available information about the pictures\n"
        "  thumbnails     print paths of all thumbnail pictures\n"
        "  sidecars       print paths of all sidecar files\n"
        "  checksums      print SHA1 checksums (output readable by sha1sum)")

        parser = optparse.OptionParser(usage)
        parser.add_option("-v", "--verbose", dest="verbosity", action="count",
                          help="increase verbosity (also multiple times)")

        # Options for the 'clone' command
        add_opts = optparse.OptionGroup(parser, "Add options",
                                 "Options for the add command.")
        add_opts.add_option("-n", "--noprocess",
                              action="store_false", dest="process_enabled",
                              help="do not process added files")
        add_opts.add_option("-r", "--recipe",
                              action="store", dest="process_recipe",
                              metavar="RECIPE",
                              help="comma sep. list of processing instructions")
        parser.add_option_group(add_opts)

        parser.set_defaults(process_enabled=True, process_recipe=None)

        opt, args = parser.parse_args(args)
        if not args:
            parser.error("no command given")
        cmd = args.pop(0)
        return cmd, args, opt.verbosity, opt.process_enabled, opt.process_recipe


    def main(self, args):
        signal.signal(signal.SIGINT, self.signal_handler)

        connector = Connector.from_string('.')
        cmd, args, verbosity, proc_enabled, recipe = self.parse_command_line(args[1:])
        app = App(connector)
        app.init_logging(verbosity)

        if cmd == "init":
            app.init()
        elif cmd == "add":
            app.add_pics(args, proc_enabled, recipe)
        elif cmd == "list":
            if not args:
                print app.list_pics(mode="all")
            else:
                print app.list_pics(mode=args[0])
        elif cmd == "test":
            import time
            while True:
                time.sleep(1)
        else:
            msg = "Invalid command: '%s'" % cmd
            self.exit_with_error(msg)

        # clean up
        logging.shutdown()

    def exit(self, code):
        sys.exit(code)

    def exit_with_error(self, msg=""):
        log.error(msg)
        self.exit(-1)

    def signal_handler(self, signum, frame):
        log.info('Caught signal %s' % signum)
        self.exit(128 + signum)

if __name__ == "__main__":
    CLI().main(sys.argv)
