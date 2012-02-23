#!/usr/bin/env python
"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import sys
import optparse
import logging

import config

from connector import Connector, LocalConnector
from recipe import Recipe
from repo import Repo
from picture import Picture
from pipeline import Pipeline

log = logging.getLogger('pic.app')

class App(object):
    """PictureClerk's command line interface."""

    def __init__(self, connector):
        self.connector = connector

    def init(self):
        repo_config = config.Config.from_dict(config.REPO_CONFIG)
        Repo.create_on_disk(self.connector, repo_config)
        self.init_repo_logging(repo_config['logging.file'],
                               repo_config['logging.format'])
        log.info("Initialized empty PictureClerk repository")

    def add_pics(self, paths, process_enabled, process_recipe=None):
        """Add pictures to repository.
        
        Arguments:
        paths           -- the picture paths to be added
        process_enabled -- boolean flag if added pictures should be processed
        process_recipe  -- recipe to use for picture processing  
        
        """
        repo = Repo.load_from_disk(self.connector)
        self.init_repo_logging(repo.config['logging.file'],
                               repo.config['logging.format'])
        pics = [Picture(path) for path in paths if os.path.exists(path)]
        repo.index.add(pics)

        # process pictures                
        if process_enabled:
            log.info("Processing pictures.")
            # set up pipeline
            if not process_recipe:
                process_recipe = Recipe.fromString(
                             repo.config['recipes.default'])
            pl = Pipeline('Pipeline1', process_recipe,
                          path=self.connector.url.path,
                          logdir=config.LOGDIR)
            for pic in pics:
                pl.put(pic)
            # process pictures
            pl.start()
            pl.join()

        log.info("Saving index to file.")
        repo.save_to_disk()

    def list_pics(self, mode):
        """Return information on pictures in repository."""
        repo = Repo.load_from_disk(self.connector)
        self.init_repo_logging(repo.config['logging.file'],
                               repo.config['logging.format'])
        if mode == "all":
            return '\n'.join(('%s' % str(pic)
                              for pic in repo.index.pics()))
        elif mode == "sidecars":
            return '\n'.join(('\n'.join(pic.get_sidecar_filenames())
                              for pic in repo.index.pics()))
        elif mode == "thumbnails":
            return '\n'.join(('\n'.join(pic.get_thumbnail_filenames())
                              for pic in repo.index.pics()))
        elif mode == "checksums":
            return '\n'.join(('%s *%s' % (pic.checksum, pic.filename)
                              for pic in repo.index.pics()))
        else:
            self.exit_with_error("Invalid list command: %s" % mode)

    def parse_command_line(self):
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

        opt, args = parser.parse_args()
        if not args:
            parser.error("no command given")
        cmd = args.pop(0)
        return cmd, args, opt.verbosity, opt.process_enabled, opt.process_recipe

    def init_logging(self, verbosity):
        """Configure logging and add console logger with supplied verbosity.
        
        Arguments:
        verbosity -- console loglevel (0 -> warning, 1 -> info, 2 -> debug)
        
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # stdout console logger
        log_level = logging.WARNING  # default
        if verbosity == 1:
            log_level = logging.INFO
        elif verbosity >= 2:
            log_level = logging.DEBUG
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(log_level)
        formatter = logging.Formatter('%(message)s')
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def init_repo_logging(self, log_file, log_format):
        # repo file logging (only if repo is local)
        if isinstance(self.connector, LocalConnector):
            log_path = os.path.join(self.connector.url.path, log_file)
            file_handler = logging.FileHandler(log_path)
            formatter = logging.Formatter(log_format)
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)

    @staticmethod
    def main():
        connector = Connector.from_string('.')
        app = App(connector)
        cmd, args, verbosity, proc_enabled, recipe = app.parse_command_line()
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
        else:
            msg = "Invalid command: '%s'" % cmd
            app.exit_with_error(msg)

        # clean up
        logging.shutdown()

    def exit_with_error(self, msg=""):
        log.error(msg)
        sys.exit(-1)

if __name__ == "__main__":
    try:
        App.main()
    except KeyboardInterrupt:
        sys.exit(None)
