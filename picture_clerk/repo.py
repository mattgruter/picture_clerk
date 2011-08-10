"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
try:
    import cPickle as pickle
except ImportError:
    import pickle

import ConfigParser

import config


class RepoNotInitializedError(Exception):
    def __init__(self, repo):
        self.repo = repo
    def __str__(self):
        return repr(self.repo)

class IndexMissingError(Exception):
    pass

class IndexParsingError(Exception):
    pass
    

class Repo(object):
    """
    PictureClerk repository
    """
    def __init__(self, connector,
                 pic_dir=config.PIC_DIR, config_file=config.CONFIG_FILE):
        self.connector = connector
        self.pic_dir = pic_dir
        self.config_file = config_file
        self.config = None
        self.index = None
        
    
    def __repr__(self):
        return "Repo(%s, %s, %s)" % (repr(self.connector), repr(self.pic_dir),
                                     repr(self.config_file))
    
    def __str__(self):
        return repr(self)
    
        
    def connect(self):
        """
        Connect to the repository.
        """        
        self.connector.connect()
        
        try:
            self.load_config()
        except IOError:
            self.connector.disconnect()
            raise RepoNotInitializedError(self)
            
            
    def disconnect(self):
        """
        Disconnect from the repository.
        """
        self.connector.disconnect()     
    
    
    def init_repo(self):
        """
        Initialize a repository
        
        create .pic directory, create a default configuration file and create
        an empty index file
        """
        # create necessary directories
        self.connector.mkdir(self.pic_dir)
        
        # create default config and write it to file
        self._create_default_config()
        self.write_config()
        
        # write empty index
        self.write_index()
        

    def _create_default_config(self):
        """
        Create ConfigParser instance with default configuration
        """
        self.config = ConfigParser.ConfigParser()
        self.config.add_section("core")
        self.config.set("core", "index_file", config.INDEX_FILE)
        self.config.set("core", "index_format_version",
                        config.INDEX_FORMAT_VERSION)
            
    
    def load_config(self):
        """
        Load the repo configuration from file.
        """
        with self.connector.open(self.config_file, 'r') as config_fh:
            # TODO: how to handle if config file does not exist?
            # TODO: check out ConfigParser's handling of defaults
            self.config = ConfigParser.ConfigParser()
            self.config.readfp(config_fh)
            
            
    def write_config(self):
        """
        Write the repo configuration to file.
        """
        with self.connector.open(self.config_file, 'w') as config_fh:
            self.config.write(config_fh)

            
    def load_index(self):
        """
        Load picture index from index file.
        """
        index_path = self.config.get("core", "index_file")
        try:
            index_fh = self.connector.open(index_path, 'rb')
        except IOError:
            raise IndexMissingError()
        try:
            self.index = pickle.load(index_fh)
        except pickle.UnpicklingError:
            raise IndexParsingError()
        finally:
            index_fh.close()

            
    def write_index(self):
        """
        Write picture index to index file
        """
        index_path = self.config.get("core", "index_file")
        with self.connector.open(index_path, 'wb') as index_fh:
            pickle.dump(self.index, index_fh)
            
    

    

