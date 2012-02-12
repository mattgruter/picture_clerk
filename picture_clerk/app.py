#!/usr/bin/env python
"""
Created on 2012/01/01

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import optparse
import logging

import config

from connector import Connector, LocalConnector
from recipe import Recipe
from repo_handler import RepoHandler
from picture import Picture
from pipeline import Pipeline

log = logging.getLogger('pic.app')

class App(object):
    """PictureClerk's command line interface."""

    def __init__(self, connector, config_file, index_file):
        self.connector = connector
        self.config_file = config_file
        self.index_file = index_file
        self.index = None
        self.repo_handler = None

    def init(self):
        repo_config = config.Config.from_dict(config.REPO_CONFIG)
        self.repo_handler = \
            RepoHandler.create_repo_on_disk(self.connector, repo_config)
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
        self.repo_handler = RepoHandler.load_repo_from_disk(self.connector)
        self.index = self.repo_handler.index
        self.init_repo_logging(self.repo_handler.config['logging.file'],
                               self.repo_handler.config['logging.format'])
        pics = [Picture(path) for path in paths if os.path.exists(path)]
        self.index.add_pictures(pics)

        # process pictures                
        if process_enabled:
            log.info("Processing pictures.")
            # set up pipeline
            if not process_recipe:
                process_recipe = Recipe.fromString(
                             self.repo_handler.config['recipes.default'])
            pl = Pipeline('Pipeline1', process_recipe,
                          path=self.connector.url.path,
                          logdir=config.LOGDIR)
            for pic in pics:
                pl.put(pic)
            # process pictures
            pl.start()
            pl.join()

        log.info("Saving index to file.")
        self.repo_handler.save_repo_index()

    def list_pics(self):
        """List pictures in repository."""
        self.repo_handler = RepoHandler.load_repo_from_disk(self.connector)
        self.index = self.repo_handler.index
        self.init_repo_logging(self.repo_handler.config['logging.file'],
                               self.repo_handler.config['logging.format'])
        for pic in sorted(self.index.get_pictures_iter()):
            print pic

    def parse_command_line(self):
        """Parse command line (sys.argv) and return the parsed args & opts.
        
        Returns:
        cmd       -- PictureClerk command (e.g. init, add, list)
        args      -- CLI positional arguments (excluding cmd)
        verbosity -- the desired logging verbosity
        
        """
        usage = "Usage: %prog [-v|--verbose] <command> [<args>]\n\n"\
        "Commands:\n"\
        "  add     add picture files to the repository\n"\
        "  init    create an empty repository\n"\
        "  list    list of pictures in repository"
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
        app = App(connector, config_file=config.CONFIG_FILE,
                  index_file=config.INDEX_FILE)
        cmd, args, verbosity, proc_enabled, recipe = app.parse_command_line()
        app.init_logging(verbosity)

        if cmd == "init":
            app.init()
        elif cmd == "add":
            app.add_pics(args, proc_enabled, recipe)
        elif cmd == "list":
            app.list_pics()
        else:
            log.error("invalid command: %s" % cmd)

        # clean up
        logging.shutdown()


if __name__ == "__main__":
    import sys
    try:
        App.main()
    except KeyboardInterrupt:
        sys.exit(None)
