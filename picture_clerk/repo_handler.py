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
    """
    RepoHandler
    """
    def __init__(self, repo, config=None):
        self.repo = repo
        self.config = config

    def load_config(self, config_fh):
        """
        Load configuration from supplied file handle.
        
        @param config_fh: readable file handle pointing to the config file
        @type config_fh: file
        """
        # @TODO: check out ConfigParser's handling of defaults
        # @TODO: make config a dict, convert to to ConfigParser when needed
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(config_fh)

    def save_config(self, config_fh):
        """
        Write configuration to supplied file handle
        
        @param config_fh: writable file handle pointing to the config file
        @type config_fh: file
        """
        self.config.write(config_fh)

    def load_index(self, index_fh):
        """
        Load (unpickle) repo's picture index from supplied file handle.
        
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
        Write (dump) repo's picture index to supplied file handle
        
        @param index_fh: writable file handle pointing to the index file
        @type index_fh: file
        """
        #@TODO: use human-readable & portable format instead of pickle
        #       e.g. json, sqlite
        pickle.dump(self.repo.index, index_fh)

    def save_repo(self, connector):
        """Save repositories configuration and index to disk."""
        try:
            connector.connect()  
            # write config to file
            with connector.open(config.CONFIG_FILE, 'w') as config_fh:
                self.save_config(config_fh)
            # write index to file
            index_filename = self.config.get('index', 'index_file')
            with connector.open(index_filename, 'wb') as index_fh:
                self.save_index(index_fh)
        finally:
            connector.disconnect()


    @staticmethod
    def create_default_config():
        """
        Create ConfigParser instance with default configuration
        """
        cp = ConfigParser.ConfigParser()
        cp.add_section("index")
        cp.set("index", "index_file", config.INDEX_FILE)
        cp.set("index", "index_format_version", str(config.INDEX_FORMAT_VERSION))
        cp.add_section("recipes")
        cp.set("recipes", "default", config.DEFAULT_RECIPE)
        return cp


    @classmethod
    def create_repo_on_disk(cls, connector, repo_config):
        """Create repo and necessary dirs according to config. Return handler.
        
        connector   -- connector to repo's base dir (created if necessary)
        repo_config -- configuration of the repository to be created
        
        """
        try:
            connector.connect()
            if not connector.exists('.'):
                connector.mkdir('.')
            connector.mkdir(config.PIC_DIR)                
            repo_handler = RepoHandler(repo.Repo(), repo_config)
            repo_handler.save_repo(connector)
        finally:
            connector.disconnect()
            
        return repo_handler
    
    
    @classmethod
    def load_repo_from_disk(cls, connector):
        """Load repository from disk. Return repository handler.
        
        connector -- connector to repo's base dir
        
        """
        try:
            connector.connect()
            if not (connector.exists('.') and connector.exists(config.PIC_DIR)):
                raise RepoNotFoundError(connector.url)
            repo_handler = RepoHandler(repo.Repo())
            
            # load config
            with connector.open(config.CONFIG_FILE, 'r') as config_fh:
                repo_handler.load_config(config_fh)            
            
            # load config    
            index_filename = repo_handler.config.get('index', 'index_file')
            with connector.open(index_filename, 'rb') as index_fh:
                repo_handler.load_index(index_fh) 
                               
        finally:
            connector.disconnect()
            
        return repo_handler


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
            
            # write config to file
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
        
            dest_rh.config = copy.deepcopy(src_rh.config)
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
        