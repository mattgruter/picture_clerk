#!/usr/bin/env python
"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import os
import sys
import logging

import config

from connector import LocalConnector
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
