"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import ConfigParser
import copy
import cPickle as pickle

import config


class IndexParsingError(Exception):
    def __init__(self, exp):
        Exception.__init__(self)
        self.orig_exp = exp
        
    def __str__(self):
        return "Error parsing index: %s" % str(self.exp)


class RepoHandler(object):
    """
    RepoHandler
    """
    def __init__(self, repo):
        self.repo = repo

    def load_config(self, config_fh):
        """
        Load repo configuration from supplied file handle.
        
        @param config_fh: readable file handle pointing to the config file
        @type config_fh: file
        """
        # @TODO: check out ConfigParser's handling of defaults
        # @TODO: make repo.config a dict, convert to to ConfigParser when needed
        self.repo.config = ConfigParser.ConfigParser()
        self.repo.config.readfp(config_fh)

    def save_config(self, config_fh):
        """
        Write repo configuration to supplied file handle
        
        @param config_fh: writable file handle pointing to the config file
        @type config_fh: file
        """
        #@TODO: make repo.config a dict, convert to to ConfigParser when needed
        self.repo.config.write(config_fh)

    def load_index(self, index_fh):
        """
        Load (unpickle) picture index from supplied file handle.
        
        @param index_fh: readable file handle pointing to the index file
        @type index_fh: file
        @raise IndexParsingError: if index can not be unpickled
        """
        try:
            self.repo.index = pickle.load(index_fh)
        except (pickle.UnpicklingError, EOFError, KeyError) as e:
            raise IndexParsingError(e)
                 
    def save_index(self, index_fh):
        """
        Write repo's picture index to index file
        
        @param index_fh: writable file handle pointing to the index file
        @type index_fh: file
        """
        #@TODO: use human-readable & portable format instead of pickle
        #       e.g. json, sqlite
        pickle.dump(self.repo.index, index_fh)

    
    @staticmethod
    def _create_default_repo_config():
        """
        Create ConfigParser instance with default configuration
        """
        cp = ConfigParser.ConfigParser()
        cp.add_section("index")
        cp.set("index", "index_file", config.INDEX_FILE)
        cp.set("index", "index_format_version", str(config.INDEX_FORMAT_VERSION))
        return cp


    @staticmethod
    def init_dir(rh, connector, create_dir=False):
        """
        Initialize the repository directory and return a Repo instance
        
        init_dir creates the necessary PictureClerk subdirectory and dumps the
        supplied index and config to disk. It also creates the repo directory
        itself if desired (repo_config=True).
        
        @param rh: repo handler instance for which the dir should be initialized
        @type rh: repo_handler.RepoHandler
        @param connector: connector to the directory to be initialized
        @type connector: connetor.Connector
        @param create_dir: set True if repo dir should be created (def.: False)
        @type create_dir: bool
        
        @return: the RepoHandler to the supplied Repo instance
        @rtype: repo_handler.RepoHandler
        """        
        try:
            connector.connect()

            # create repo dir (optional)
            if create_dir:
                connector.mkdir('.')

            # create necessary directories
            connector.mkdir(config.PIC_DIR)

            # write repo_config to file
            #with connector.open(config_file, 'wb') as config_fh:    
            config_fh = connector.open(config.CONFIG_FILE, 'wb')
            try:
                rh.save_config(config_fh)
            finally:
                config_fh.close()
            
            # write index to file
            #with connector.open(config.INDEX_FILE, 'wb') as index_fh:
            index_fh = connector.open(config.INDEX_FILE, 'wb')
            try:
                rh.save_index(index_fh)
            finally:
                index_fh.close()
            
        except:
            connector.disconnect()
            raise
    
                
    @staticmethod
    def clone_repo(src_rh, src_connector, dest_rh, dest_connector):
        """
        Clone an existing repository to a new location
        
        @param src_rh: the repo handler of the source repo
        @type src_rh: repo_handler.RepoHandler
        @param src_connector: the connector to the src_repo dir
        @type src_connector: connector.Connector
        @param dest_rh: the repo handler of the destination repo
        @type dest_rh: repo_handler.RepoHandler
        @param dest_connector: connector pointing to the location of the new
                               clone-repo
        @type dest_connector: connector.Connector
        """
        
        try:
            src_connector.connect()
            
            # read src_repo's configuration
            #with connector.open(config_file, 'rb') as config_fh:    
            config_fh = src_connector.open(config.CONFIG_FILE, 'rb')
            try:
                src_rh.load_config(config_fh)
            finally:
                config_fh.close()
            
            # read src_repo's index 
            #with connector.open(index_file, 'rb') as config_fh:    
            index_fh = src_connector.open(config.INDEX_FILE, 'rb')
            try:
                src_rh.load_index(index_fh)
            finally:
                config_fh.close()
        
            dest_rh.repo.config = copy.deepcopy(src_rh.repo.config)
            dest_rh.repo.index = copy.deepcopy(src_rh.repo.index)
            RepoHandler.init_dir(dest_rh, dest_connector, create_dir=True)
            
            # @FIXME: dest_connector will be connected/disconnected many times
            #         during cloning: once by init_dir and once for each
            #         file to copy --> not very efficient!
            for picture in src_rh.repo.index:
                for fname in picture.get_filenames():
                    src_connector.copy(fname, dest_connector, dest=fname)
                    
        finally:   
            src_connector.disconnect()
            dest_connector.disconnect()
        