"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import copy
import cPickle as pickle

import config
import repo

class RepoNotFoundError(Exception):
    def __init__(self, url):
        Exception.__init__(self)
        self.url = url
    def __str__(self):
        return "No repository found at %s" % self.url.geturl()

class IndexParsingError(Exception):
    def __init__(self, exp):
        Exception.__init__(self)
        self.orig_exp = exp
    def __str__(self):
        return "Error parsing index: %s" % str(self.exp)


class RepoHandler(object):

    def __init__(self, repo, config, connector):
        """RepoHandler helps administration of repositories.
        
        There are methods for creating a new repository directory structure,
        loading an existing repository from disk, loading and saving repo
        index & configuration and cloning an existing repository.
        
        repo      -- Repo instance
        config    -- repository specific configuration (type ConfigParser)
        connector -- Connector instance pointing to repo's location
        
        """
        self.repo = repo
        self.config = config
        self.connector = connector

    def read_index(self, fh):
        """Load and return repo's picture index from supplied file handle.
        
        Arguments:
        fh -- readable file handle pointing to the index file
        
        Raises:
        IndexParsingError if index can not be unpickled
        
        """
        try:
            index = pickle.load(fh)
        except (pickle.UnpicklingError, EOFError, KeyError) as e:
            raise IndexParsingError(e)
        return index

    def dump_index(self, index, fh):
        """Dump repo's picture index to supplied file handle.
        
        Arguments:
        
        fh -- writable file handle

        """
        # @TODO: use human-readable & portable format/store instead of pickle
        #        e.g. json, sqlite
        pickle.dump(index, fh)

    def load_repo_index(self):
        try:
            self.connector.connect()
            index_filename = self.config['index.file']
            with self.open(index_filename, 'rb') as index_fh:
                self.repo.index = self.read_index(index_fh)
        except: # disconnect in case of exception, otherwise stay connected
            self.connector.disconnect()
            raise

    def save_repo_index(self):
        """Save repository picture index to disk."""
        try:
            self.connector.connect()
            index_filename = self.config['index.file']
            with self.connector.open(index_filename, 'wb') as index_fh:
                self.dump_index(self.repo.index, index_fh)
        except: # disconnect in case of exception, otherwise stay connected
            self.connector.disconnect()
            raise


    @classmethod
    def create_repo_on_disk(cls, connector, conf):
        """Create repo and necessary dirs according to config. Return handler.
        
        connector -- connector to repo's base dir (created if necessary)
        conf      -- repository specific configuration
        
        """
        try:
            connector.connect()
            if not connector.exists('.'):
                connector.mkdir('.')
            connector.mkdir(config.PIC_DIR)
            handler = RepoHandler(repo.Repo(), conf, connector)
            with connector.open(config.CONFIG_FILE, 'w') as config_fh:
                handler.config.write(config_fh)

            handler.save_repo_index()
        finally:
            connector.disconnect()
        return handler

    @classmethod
    def load_repo_from_disk(cls, connector):
        """Load repository from disk. Return repository handler.
        
        connector -- connector to repo's base dir
        
        """
        try:
            connector.connect()
            if not (connector.exists('.') and connector.exists(config.PIC_DIR)):
                raise RepoNotFoundError(connector.url)
            handler = RepoHandler(repo.Repo(), config.Config(), connector)

            # load config
            with connector.open(config.CONFIG_FILE, 'r') as config_fh:
                handler.config.read(config_fh)

            # load index    
            index_filename = handler.config['index.file']
            with connector.open(index_filename, 'rb') as index_fh:
                handler.repo.index = handler.read_index(index_fh)

        finally:
            connector.disconnect()

        return handler

    @classmethod
    def clone_repo(cls, src, dest):
        """Clone an existing repository to a new location and return handler.
        
        src  -- connector pointing to source repo's location
        dest -- connector pointing to location of new clone-repo
        
        """
        # clone repo & handler
        src_handler = RepoHandler.load_repo_from_disk(src)
        conf = copy.deepcopy(src_handler.config)
        handler = RepoHandler.create_repo_on_disk(conf, dest)
        handler.repo.index = copy.deepcopy(src_handler.repo.index)

        # clone pictures
        # @FIXME: dest will be connected/disconnected many times during cloning
        #         once above and once for each file to copy!
        try:
            src.connect()
            dest.disconnect()
            for picture in src_handler.repo.index:
                for fname in picture.get_filenames():
                    src.copy(fname, dest, dest=fname)
        finally:
            src.disconnect()
            dest.disconnect()

        return handler
