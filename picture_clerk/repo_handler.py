"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import copy

import config
import index

class RepoNotFoundError(Exception):
    def __init__(self, url):
        Exception.__init__(self)
        self.url = url
    def __str__(self):
        return "No repository found at %s" % self.url.geturl()


class RepoHandler(object):

    def __init__(self, index, config, connector):
        """RepoHandler helps administration of repositories.
        
        There are methods for creating a new repository directory structure,
        loading an existing repository from disk, loading and saving index &
        configuration and cloning an existing repository.
        
        index      -- PictureIndex instance
        config    -- repository specific configuration (type ConfigParser)
        connector -- Connector instance pointing to index's location
        
        """
        self.index = index
        self.config = config
        self.connector = connector

    def load_repo_index(self):
        try:
            self.connector.connect()
            index_filename = self.config['index.file']
            with self.open(index_filename, 'rb') as index_fh:
                self.index.read(index_fh)
        except: # disconnect in case of exception, otherwise stay connected
            self.connector.disconnect()
            raise

    def save_repo_index(self):
        """Save picture index to disk."""
        try:
            self.connector.connect()
            index_filename = self.config['index.file']
            with self.connector.open(index_filename, 'wb') as index_fh:
                self.index.write(index_fh)
        except: # disconnect in case of exception, otherwise stay connected
            self.connector.disconnect()
            raise


    @classmethod
    def create_repo_on_disk(cls, connector, conf):
        """Create repo and necessary dirs according to config. Return handler.
        
        connector -- connector to index's base dir (created if necessary)
        conf      -- repository specific configuration
        
        """
        try:
            connector.connect()
            if not connector.exists('.'):
                connector.mkdir('.')
            connector.mkdir(config.PIC_DIR)
            with connector.open(config.CONFIG_FILE, 'w') as config_fh:
                conf.write(config_fh)
            handler = RepoHandler(index.PictureIndex(), conf, connector)
            handler.save_repo_index()
        finally:
            connector.disconnect()
        return handler

    @classmethod
    def load_repo_from_disk(cls, connector):
        """Load configuration & repository from disk. Return repository handler.
        
        connector -- connector to index's base dir
        
        """
        try:
            connector.connect()
            if not (connector.exists('.') and connector.exists(config.PIC_DIR)):
                raise RepoNotFoundError(connector.url)
            # load config
            conf = config.Config(config.REPO_CONFIG)
            with connector.open(config.CONFIG_FILE, 'r') as config_fh:
                conf.read(config_fh)
            # load index
            pic_index = index.PictureIndex()
            index_filename = conf['index.file']
            with connector.open(index_filename, 'rb') as index_fh:
                pic_index.read(index_fh)
        finally:
            connector.disconnect()
        return RepoHandler(pic_index, conf, connector)

    @classmethod
    def clone_repo(cls, src, dest):
        """Clone an existing repository to a new location and return handler.
        
        src  -- connector pointing to source repo's location
        dest -- connector pointing to location of new clone-index
        
        """
        # clone repo & handler
        src_handler = RepoHandler.load_repo_from_disk(src)
        conf = copy.deepcopy(src_handler.config)
        handler = RepoHandler.create_repo_on_disk(conf, dest)
        handler.index.index = copy.deepcopy(src_handler.index.index)

        # clone pictures
        # @FIXME: dest will be connected/disconnected many times during cloning
        #         once above and once for each file to copy!
        try:
            src.connect()
            dest.disconnect()
            for picture in src_handler.index.index:
                for fname in picture.get_filenames():
                    src.copy(fname, dest, dest=fname)
        finally:
            src.disconnect()
            dest.disconnect()

        return handler
