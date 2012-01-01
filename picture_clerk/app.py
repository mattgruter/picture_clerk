#!/usr/bin/env python
"""
Created on 2012/01/01

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import os
import optparse

import config

from path import Path
from local_connector import LocalConnector
from repo import Repo
from repo_handler import RepoHandler
from picture import Picture


class App(object):
    def __init__(self, connector,
                 config_file=config.CONFIG_FILE, index_file=config.INDEX_FILE):
        self.connector = connector
        self.config_file = config_file
        self.index_file = index_file
        self.repo = None
        self.repo_handler = None

    def _load_config_from_disk(self):
        self.connector.connect()
        with self.connector.open(self.config_file, 'r') as config_fh:
            self.repo_handler.load_config(config_fh)
            
    def _dump_config_to_disk(self):
        self.connector.connect()
        with self.connector.open(self.config_file, 'w') as config_fh:
            self.repo_handler.save_config(config_fh)
        
    def _load_index_from_disk(self):
        self.connector.connect()
        with self.connector.open(self.index_file, 'r') as index_fh:
            self.repo_handler.load_index(index_fh)
        
    def _save_index_to_disk(self):
        self.connector.connect()
        with self.connector.open(self.index_file, 'w') as index_fh:
            self.repo_handler.save_index(index_fh)
        
    def init(self):
        self.repo = Repo()
        self.repo_handler = RepoHandler(self.repo,
                                        RepoHandler.create_default_config())
        RepoHandler.init_dir(self.repo_handler, self.connector)
        
    def add(self, paths):
        self.repo = Repo()
        self.repo_handler = RepoHandler(self.repo)
        self._load_config_from_disk()
        self._load_index_from_disk()
        for path in paths:
            if os.path.exists(path):
                pic = Picture(path)
                self.repo.add_picture(pic)
        self._save_index_to_disk()
        
    def list_pics(self):
        self.repo = Repo()
        self.repo_handler = RepoHandler(self.repo)
        self._load_config_from_disk()
        self._load_index_from_disk()
        for pic in sorted(self.repo.index):
            print pic


    @staticmethod
    def main():    
        usage = "Usage: %prog [-v|--verbose] <command> [<args>]\n\n" \
                "Commands:\n" \
                "  add    add picture files to the repository\n" \
                "  init   create an empty repository\n" \
                "  list   show list of pictures in repository"
        parser = optparse.OptionParser(usage)
        parser.add_option("-v", "--verbose",
                          action="store_true", dest="verbose",
                          help="make lots of noise")
        (opt, args) = parser.parse_args()
        if not args:
            parser.error("no command given")
        cmd = args.pop(0)
       
        path = Path.fromPath('.')
        connector = LocalConnector(path)
        app = App(connector)
        if cmd == "init":
            app.init()
        elif cmd == "add":
            app.add(args)
        elif cmd == "list":
            app.list_pics()
        else:
            parser.error("invalid command: %s" % cmd)
                
        
if __name__ == "__main__":
    import sys
    try:
        App.main()
    except KeyboardInterrupt:
        sys.exit(None)
